import ckan
from ckan.plugins import SingletonPlugin, implements, IPackageController
import pylons
from pylons import config

LANGS = ['en', 'fr', 'de', 'es', 'it', 'nl', 'ro', 'pt', 'pl']

class MultilingualDataset(SingletonPlugin):
    implements(IPackageController, inherit=True)

    def before_index(self, search_params):
        return search_params

    def before_search(self, search_params):
        lang_set = set(LANGS)
        current_lang = pylons.request.environ['CKAN_LANG']
        # fallback to default locale if locale not in suported langs
        if not current_lang in lang_set:
            current_lang = config.get('ckan.locale_default')
        # fallback to english if default locale is not supported
        if not current_lang in lang_set:
            current_lang = 'en'
        # treat current lang differenly so remove from set
        lang_set.remove(current_lang)

        # weight current lang more highly
        query_fields = 'title_%s^8 text_%s^4' % (current_lang, current_lang)

        for lang in lang_set:
            query_fields += ' title_%s^2 text_%s' % (lang, lang)

        search_params['qf'] = query_fields

        return search_params

    # FIXME: Look for translation in fallback language when none found in
    # desired language.
    def before_view(self, data_dict):
        desired_lang_code = pylons.request.environ['CKAN_LANG']
        fallback_lang_code = pylons.config.get('ckan.locale_default', 'en')

        # Get a flattened copy of data_dict to do the translation on.
        flattened = ckan.lib.navl.dictization_functions.flatten_dict(
                data_dict)

        # Get a simple flat list of all the terms to be translated, from the
        # flattened data dict.
        from sets import Set
        terms = Set()
        for (key, value) in flattened.items():
            if value in (None, True, False):
                continue
            elif isinstance(value, basestring):
                terms.add(value)
            else:
                for item in value:
                    terms.add(item)

        # Get the translations of all the terms (as a list of dictionaries).
        translations = ckan.logic.action.get.term_translation_show(
                {'model': ckan.model},
                {'terms': terms,
                    'lang_codes': (desired_lang_code, fallback_lang_code)})

        # Transform the translations into a more convenient structure.
        desired_translations = {}
        fallback_translations = {}
        for translation in translations:
            if translation['lang_code'] == desired_lang_code:
                desired_translations[translation['term']] = (
                        translation['term_translation'])
            else:
                assert translation['lang_code'] == fallback_lang_code
                fallback_translations[translation['term']] = (
                        translation['term_translation'])

        # Make a copy of the flattened data dict with all the terms replaced by
        # their translations, where available.
        translated_flattened = {}
        for (key, value) in flattened.items():
            if key[0] in ('tags', 'groups') and key[2] == 'name':
                # Don't translate names that are used to form URLs
                translated_flattened[key] = value
            elif value in (None, True, False):
                translated_flattened[key] = value
            elif isinstance(value, basestring):
                if desired_translations.has_key(value):
                    translated_flattened[key] = desired_translations[value]
                else:
                    translated_flattened[key] = fallback_translations.get(
                            value, value)
            else:
                translated_value = []
                for item in value:
                    if desired_translations.has_key(value):
                        translated_flattened[key] = desired_translations[value]
                    else:
                        translated_flattened[key] = fallback_translations.get(
                                value, value)
                translated_flattened[key] = translated_value

        # Finally unflatten and return the translated data dict.
        translated_data_dict = (ckan.lib.navl.dictization_functions
                .unflatten(translated_flattened))
        return translated_data_dict

class MultilingualGroup(SingletonPlugin):
    implements(IPackageController, inherit=True)

    def before_view(self, data_dict):
        return data_dict
