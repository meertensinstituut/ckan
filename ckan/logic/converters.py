from pylons.i18n import _
from ckan import model
from ckan.model import vocabulary
from ckan.lib.navl.dictization_functions import Invalid
from ckan.lib.field_types import DateType, DateConvertError
from ckan.logic.validators import tag_length_validator, tag_name_validator

def convert_to_extras(key, data, errors, context):
    extras = data.get(('extras',), [])
    if not extras:
        data[('extras',)] = extras
    extras.append({'key': key[-1], 'value': data[key]})

def convert_from_extras(key, data, errors, context):
    for data_key, data_value in data.iteritems():
        if (data_key[0] == 'extras'
            and data_key[-1] == 'key'
            and data_value == key[-1]):
            data[key] = data[('extras', data_key[1], 'value')]

def date_to_db(value, context):
    try:
        value = DateType.form_to_db(value)
    except DateConvertError, e:
        raise Invalid(str(e))
    return value

def date_to_form(value, context):
    try:
        value = DateType.db_to_form(value)
    except DateConvertError, e:
        raise Invalid(str(e))
    return value

def convert_to_tags(vocab):
    def callable(key, data, errors, context):
        tag_string = data.get(key)
        new_tags = [tag.strip() for tag in tag_string.split(',') if tag.strip()]
        if not new_tags:
            return
        # get current number of tags
        n = 0
        for k in data.keys():
            if k[0] == 'tags':
                n = max(n, k[1] + 1)

        for tag in new_tags:
            tag_length_validator(tag, context)
            tag_name_validator(tag, context)
        v = model.Vocabulary.get(vocab)
        if not v:
            raise Invalid(_('Tag vocabulary "%s" does not exist') % vocab)

        for num, tag in enumerate(new_tags):
            data[('tags', num+n, 'name')] = tag
            data[('tags', num+n, 'vocabulary_id')] = v.id
    return callable

def convert_from_tags(vocab):
    def callable(key, data, errors, context):
        v = model.Vocabulary.get(vocab)
        if not v:
            raise Invalid(_('Tag vocabulary "%s" does not exist') % vocab)

        tags = {}
        for k in data.keys():
            if k[0] == 'tags':
                if data[k].get('vocabulary_id') == v.id:
                    tags[k] = data[k]

        # TODO: vocab tags should be removed in a separate converter (and by default) 'tags'
        for k in tags.keys():
            del data[k]
        data[key] = ', '.join([t['name'] for t in tags.values()])

    return callable

