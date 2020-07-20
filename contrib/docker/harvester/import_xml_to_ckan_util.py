# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import urllib2
import json
from pprint import pprint

import requests
import hashlib
import datetime

conf_file_path = 'importer-conf.json'
apikey = ''
orgs = dict()
debug = False
qty = 10
spatial_exists = False
machine_translation_target_path = ''
machine_translation_target = ''


def init():
    global apikey
    global orgs
    global debug
    global qty
    global spatial_exists
    global machine_translation_target_path
    global machine_translation_target

    try:
        with open(conf_file_path, 'r') as conf_file:
            conf = json.load(conf_file)

            apikey = conf['apikey']
            orgs = conf['orgs']
            debug = conf['debug']
            qty = conf['qty']
            spatial_exists = conf['spatial_exists']
            machine_translation_target_path = conf['machine_translation_target_path']
            machine_translation_target = conf['machine_translation_target']
    except Exception as ex:
        exit('Error occurred during loading and parsing of importer config file: {}'.format(ex.message))


def set_title_homepage_style():
    dataset_dict = {
        'ckan.site_title': 'ISEBEL',
        'ckan.homepage_style': 4
    }

    # Use the json module to dump the dictionary to a string for posting.
    data_string = urllib2.quote(json.dumps(dataset_dict))

    request = urllib2.Request(
        'http://ckan:5000/api/3/action/config_option_update')

    # Creating a dataset requires an authorization header.
    request.add_header('Authorization', apikey)

    # Make the HTTP request.
    response = urllib2.urlopen(request, data_string)
    assert response.code == 200

    # Use the json module to load CKAN's response into a dictionary.
    response_dict = json.loads(response.read())
    if response_dict['success'] is True:
        return True
    else:
        return False


def create_org(orgKey):
    dataset_dict = {
        'title': orgs[orgKey][0],
        'name': orgs[orgKey][1],
        'id': orgs[orgKey][1],
        'image_url': orgs[orgKey][2]
    }

    # Use the json module to dump the dictionary to a string for posting.
    data_string = urllib2.quote(json.dumps(dataset_dict))

    # We'll use the package_create function to create a new dataset.
    request = urllib2.Request(
        'http://ckan:5000/api/3/action/organization_create')

    # Creating a dataset requires an authorization header.
    request.add_header('Authorization', apikey)

    # Make the HTTP request.
    response = urllib2.urlopen(request, data_string)
    assert response.code == 200

    # Use the json module to load CKAN's response into a dictionary.
    response_dict = json.loads(response.read())
    if response_dict['success'] is True:
        return True
    else:
        return False


def org_exists(orgKey):
    request = urllib2.Request('http://ckan:5000/api/3/action/organization_show?id=%s' % orgKey)
    # Make the HTTP request.
    try:
        urllib2.urlopen(request)
    except:
        print('%s does not exist' % orgKey)
        return False

    print('%s exists.' % orgKey)
    return True


def isdate(date_text, date_format='%Y-%m-%d'):
    try:
        datetime.datetime.strptime(date_text, date_format)
        return True
    except ValueError:
        # raise ValueError("Incorrect data format, should be YYYY-MM-DD")
        return False


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_created_package(org, apikey, maxrows=1000):
    request = urllib2.Request('http://ckan:5000/api/3/action/package_search?q=organization:%s&rows=%s' % (org, maxrows))
    request.add_header('Authorization', apikey)

    # Make the HTTP request.
    response = urllib2.urlopen(request)
    assert response.code == 200

    # Use the json module to load CKAN's response into a dictionary.
    response_dict = json.loads(response.read())
    assert response_dict['success'] is True

    # package_create returns the created package as its result.
    results = response_dict['result']['results']
    created_package = list()
    for result in results:
        created_package.append(result['name'])

    return created_package


def get_all_created_package(apikey):
    request = urllib2.Request('http://ckan:5000/api/3/action/package_list')
    request.add_header('Authorization', apikey)

    # Make the HTTP request.
    response = urllib2.urlopen(request)
    assert response.code == 200

    # Use the json module to load CKAN's response into a dictionary.
    response_dict = json.loads(response.read())
    assert response_dict['success'] is True

    # package_create returns the created package as its result.
    created_package = response_dict['result']

    return created_package


def remove_all_created_package(created_package, apikey, clear=True):
    # TODO: when there is conflict, the dataset will not be removed. solve this either in solr or in ckan
    # TODO: test if can purge in batch mode
    for i in created_package:
        dataset_dict = {'id': i}
        # print('removing package: [%s]' % i)

        response_delete = None
        response_purge = None
        try:
            # delete dataset, then it can be purged
            response_delete = requests.post('http://ckan:5000/api/3/action/package_delete',
                                            data=dataset_dict,
                                            headers={"X-CKAN-API-Key": apikey})

            # purge dataset
            response_purge = requests.post('http://ckan:5000/api/3/action/dataset_purge',
                                           data=dataset_dict,
                                           headers={"X-CKAN-API-Key": apikey})
        except Exception as ex:
            if response_delete and response_purge:
                print('Error occurred[{}]! Deletion: {}; Purge: {}; data: {}'.format(ex.message,
                                                                                     response_delete.status_code,
                                                                                     response_purge.status_code, i))
            elif response_delete:
                print('Error occurred[{}]! Deletion: {}; Purge: {}; data: {}'.format(ex.message,
                                                                                     response_delete.status_code,
                                                                                     response_purge, i))
            elif response_purge:
                print('Error occurred[{}]! Deletion: {}; Purge: {}; data: {}'.format(ex.message, response_delete,
                                                                                     response_purge.status_code, i))
            if not clear:
                exit('Exiting due to error! With clear set to True, importing can continue ignoring error!')
    return True


def get_package_by_id(id, apikey):
    request = urllib2.Request('http://ckan:5000/api/3/action/package_show?id=%s' % id)
    request.add_header('Authorization', apikey)
    # Make the HTTP request.
    response = None
    try:
        response = urllib2.urlopen(request)
    except Exception as e:
        return None

    if response and response.code == 200:
        # Use the json module to load CKAN's response into a dictionary.
        response_dict = json.loads(response.read())
        assert response_dict['success'] is True

        return response_dict

    return None


def update_package_by_id(id, apikey, dataset_dict):
    print("calling remote API to update")
    request = urllib2.Request('http://ckan:5000/api/3/action/package_patch?id=%s' % id)
    request.add_header('Authorization', apikey)
    data_string = urllib2.quote(json.dumps(dataset_dict))

    # Make the HTTP request.
    response = None
    try:
        response = urllib2.urlopen(request, data_string)
    except Exception as e:
        print(e)
        print(dataset_dict)
        exit("remote call failed")

    if response and response.code == 200:
        # Use the json module to load CKAN's response into a dictionary.
        response_dict = json.loads(response.read())
        assert response_dict['success'] is True
        return response_dict

    # exit("remote response return code is not 200: {}".format(response))
    return None


def get_package_by_name(name, apikey):
    request = urllib2.Request('http://ckan:5000/api/3/action/package_show?name=%s' % name)
    request.add_header('Authorization', apikey)

    # Make the HTTP request.
    response = None
    try:
        response = urllib2.urlopen(request)
    except Exception as e:
        print(e.message)

    if response and response.code == 200:
        # Use the json module to load CKAN's response into a dictionary.
        response_dict = json.loads(response.read())
        assert response_dict['success'] is True

        return response_dict

    return None


def write_persons_to_dataset(persons_dict, dataset_dict):
    for k, v in persons_dict.iteritems():
        dataset_dict['extras'].append(
            {'key': k,
             'value': '; '.join([i for i in v if i is not ''])})


def process_persons_list(persons):
    persons_dict = dict()
    first_run = True
    for person in persons:
        if first_run:
            persons_dict = process_persons_dict(person)
            first_run = False
        else:
            merge_dict(persons_dict, (process_persons_dict(person)))
    return persons_dict


def process_persons_dict(persons):
    persons_dict = dict()

    def process_person_role(p, r):
        # p stands for person
        # r stands for role of person
        # k is the current key
        # v is the current value associate with the key
        k = 'person_{}'.format(r)
        v = p.get('name').get('$') if p.get('name') is not None else p.get('@id')

        if k not in persons_dict.keys():
            persons_dict[k] = list()
        persons_dict[k].append(v)

        if '{}_gender'.format(k) not in persons_dict.keys():
            persons_dict['{}_gender'.format(k)] = list()
        persons_dict['{}_gender'.format(k)].append(persons.get('gender').get('$') if persons.get('gender') else '')

    if isinstance(persons.get('role'), dict):
        role = persons.get('role').get('$')
        process_person_role(persons, role)
    elif isinstance(persons.get('role'), list):
        for role_dict in persons.get('role'):
            role = role_dict.get('$')
            process_person_role(persons, role)
    else:
        return None

    return persons_dict


def write_places_to_dataset(places_dict, dataset_dict):
    for k, v in places_dict.iteritems():
        if k == 'geopoints':
            dataset_dict['extras'].append(
                {'key': 'spatial',
                 'value': json.dumps({'type': 'MultiPoint',
                                      'coordinates': v})})
        else:
            dataset_dict['extras'].append(
                {'key': k,
                 'value': '; '.join([i for i in v if i is not ''])})


def process_places_dict(places):
    places_dict = dict()

    def process_place_role(p, r):
        # p stands for place
        # r stands for role of place
        # k is the current key
        # v is the current value associate with the key
        k = 'place_{}'.format(r)
        v = p.get('title').get('$') if p.get('title') is not None else p.get('@id')

        if k not in places_dict.keys():
            places_dict[k] = list()
        places_dict[k].append(u'{}'.format(v))

        if 'geopoints' not in places_dict.keys():
            places_dict['geopoints'] = list()

        if p.get('point') is not None and \
            p.get('point').get('pointLongitude') is not None and \
            p.get('point').get('pointLatitude') is not None:
            places_dict['geopoints'].append([float(p.get('point').get('pointLongitude').get('$')),
                                             float(p.get('point').get('pointLatitude').get('$'))])

    if isinstance(places.get('role'), dict):
        role = places.get('role').get('$')
        process_place_role(places, role)
    elif isinstance(places.get('role'), list):
        for role_dict in places.get('role'):
            role = role_dict.get('$')
            process_place_role(places, role)
    else:
        return None

    return places_dict


def process_places_list(places):
    places_dict = dict()
    first_run = True
    for place in places:
        if first_run:
            places_dict = process_places_dict(place)
            first_run = False
        else:
            merge_dict(places_dict, process_places_dict(place))
            # places_dict.update(process_places_dict(place))
    return places_dict


def merge_dict(dict1, dict2):
    for k, v in dict2.iteritems():
        if k in dict1.keys():
            dict1[k] = dict1[k] + v
        else:
            dict1[k] = v
    return dict1


def get_new_translation_from_file(full_path):
    try:
        with open(full_path, 'r') as fh:
            print('New translation found!')
            return ''.join([line.decode('utf-8') for line in fh.readlines()])
    except IOError:
        return None


def set_extra_data_field(apikey, story_global_identifier, field, new_value):
    print("updating...")
    dataset_dict = get_package_by_id(story_global_identifier, apikey)
    if not dataset_dict:
        print("Package {} not found".format(story_global_identifier))
        return False

    extras_list = dataset_dict.get('result').get('extras') if dataset_dict else None
    if extras_list and isinstance(extras_list, list):
        for item_dict in extras_list:
            k = item_dict.get('key').encode('utf-8')

            # remove empty spatial info as well as the current field to be updated
            if k == field or k == 'spatial':
                # check if the field exists, if so, remove the old one
                extras_list.remove(item_dict)

        # set the field to the new value
        print("setting new value")
        extras_list.append({'key': field, 'value': new_value})
        dataset_dict['extras'] = extras_list
        dataset_dict['id'] = story_global_identifier.replace('.', '-')
        update_package_by_id(story_global_identifier.replace('.', '-'), apikey, dataset_dict)
        return True

    return False


def get_extra_data_field(apikey, story_global_identifier, field, lang=False):
    # dataset_dict = get_package_by_id(story_global_identifier.replace('.', '-'), apikey)
    dataset_dict = get_package_by_id(story_global_identifier, apikey)
    if dataset_dict is None:
        return 'no record'

    extras_list = dataset_dict.get('result').get('extras') if dataset_dict else None
    if extras_list and isinstance(extras_list, list):
        if lang:
            for item_dict in extras_list:
                k = item_dict.get('key').encode('utf-8')
                v = item_dict.get('value').encode('utf-8')
                if k in field:
                    return v
        else:
            for item_dict in extras_list:
                k = item_dict.get('key').encode('utf-8')
                v = item_dict.get('value').encode('utf-8')
                if k == field:
                    return v
    return None
