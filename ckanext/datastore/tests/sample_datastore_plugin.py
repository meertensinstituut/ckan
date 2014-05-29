import ckan.plugins as p

import ckanext.datastore.interfaces as interfaces


class SampleDataStorePlugin(p.SingletonPlugin):
    p.implements(interfaces.IDatastore, inherit=True)

    def validate_query(self, context, data_dict, all_field_ids):
        valid_filters = ('age_between', 'age_not_between')
        filters = data_dict.get('filters', {})
        for key in filters.keys():
            if key in valid_filters:
                del filters[key]

        return data_dict

    def search_data(self, context, data_dict, all_field_ids, query_dict):
        query_dict['where'] += self._where(data_dict)
        return query_dict

    def delete_data(self, context, data_dict, all_field_ids, query_dict):
        query_dict['where'] += self._where(data_dict)
        return query_dict

    def _where(self, data_dict):
        filters = data_dict.get('filters', {})
        where_clauses = []

        if 'age_between' in filters:
            age_between = filters['age_between']

            clause = ('"age" >= %s AND "age" <= %s',
                      age_between[0], age_between[1])
            where_clauses.append(clause)
        if 'age_not_between' in filters:
            age_not_between = filters['age_not_between']

            clause = ('"age" < %s OR "age" > %s',
                      age_not_between[0], age_not_between[1])
            where_clauses.append(clause)

        return where_clauses
