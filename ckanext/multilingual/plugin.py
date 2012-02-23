import ckan
from ckan.plugins import SingletonPlugin, implements, IPackageController
import pylons

class MultilingualDataset(SingletonPlugin):
    implements(IPackageController, inherit=True)

    def before_index(self, search_params):
        return search_params

    def before_search(self, search_params):
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
            if value in (None, True, False):
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
