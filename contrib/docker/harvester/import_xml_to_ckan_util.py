# -*- coding: utf-8 -*-
import urllib2
import json
from pprint import pprint

import requests
import hashlib
import datetime

apikey = '14aff969-a909-4947-bb4c-e0383829213d'
orgs = {
    'meertens': ['Meertens Institute', 'meertens'],
    'ucla': ['UCLA', 'ucla'],
    'wossidia': ['Wossidia', 'wossidia']
}
debug = False
qty = 99999


def set_title_homepage_style():
    dataset_dict = {
        'ckan.site_title': 'ISEBEL',
        'ckan.homepage_style': 2
    }

    # Use the json module to dump the dictionary to a string for posting.
    data_string = urllib2.quote(json.dumps(dataset_dict))

    # We'll use the package_create function to create a new dataset.
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
        'id': orgs[orgKey][1]
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
    print 'http://ckan:5000/api/3/action/organization_show?id=%s' % orgKey
    request = urllib2.Request('http://ckan:5000/api/3/action/organization_show?id=%s' % orgKey)
    # Make the HTTP request.
    try:
        urllib2.urlopen(request)
    except Exception as e:
        print '%s does not exist' % orgKey
        return False

    print '%s exists.' % orgKey
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


def remove_all_created_package(created_package, apikey):
    for i in created_package:
        dataset_dict = {'id': i}
        # print('removing package: [%s]' % i)
        response = requests.post('http://ckan:5000/api/3/action/package_delete',
                      data=dataset_dict,
                      headers={"X-CKAN-API-Key": apikey})
        assert response.status_code == 200, 'Error occurred: %s; data: %s' % (response.content, i)
        # purge dataset
        response = requests.post('http://ckan:5000/api/3/action/dataset_purge',
                      data=dataset_dict,
                      headers={"X-CKAN-API-Key": apikey})
        assert response.status_code == 200, 'Error occurred: %s; data: %s' % (response.content, i)

    return True


def get_package_by_id(id, apikey):
    request = urllib2.Request('http://ckan:5000/api/3/action/package_show?id=%s' % id)
    request.add_header('Authorization', apikey)

    # Make the HTTP request.
    response = None
    try:
        response = urllib2.urlopen(request)
    except Exception as e:
        print e.message

    if response:
        if response.code == 200:
            # Use the json module to load CKAN's response into a dictionary.
            response_dict = json.loads(response.read())
            assert response_dict['success'] is True

            pprint(response_dict)
            return response_dict

    return None
