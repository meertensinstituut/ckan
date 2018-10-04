# -*- coding: utf-8 -*-
import urllib2
import urllib
import json
import requests
import xml.etree.ElementTree as et
import hashlib
from os import listdir
from os.path import isfile, join
import unicodedata
from pprint import pprint
import time


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_created_package(org, apikey):
    request = urllib2.Request('http://ckan:5000/api/3/action/package_search?q=organization:%s' % org)
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


def remove_all_created_package(created_package, apikey):
    for i in created_package:
        dataset_dict = {'id': i}
        requests.post('http://ckan:5000/api/3/action/package_delete',
                      data=dataset_dict,
                      headers={"X-CKAN-API-Key": apikey})
        # purge dataset
        requests.post('http://ckan:5000/api/3/action/dataset_purge',
                      data=dataset_dict,
                      headers={"X-CKAN-API-Key": apikey})


class XML():
    isebel_list = ['text', 'identifier', 'url', 'datePublished', 'narrator', 'placeOfNarration', 'placeMentioned']
    data = dict()

    def get_element(self, tree, isebel_list = isebel_list):
        for i in isebel_list:
            tmp = tree.find(i)
            self.data[i] = tmp.text if tmp is not None else None

    def forward_geocoding(self, place, mapkey):
        # check if place is unicode
        # if unicode encode continue with the code, if str, skip next command
        print 'original place name: %s' % place.encode('utf-8')
        if type(place) is not str:
            place = urllib.quote(unicodedata.normalize('NFKD', place).encode('ascii', 'ignore'))
        else:
            place = urllib.quote(place)
        print 'place name: %s' % place
        url = 'https://api.mapbox.com/geocoding/v5/mapbox.places/%s.json?access_token=%s' % (place, mapkey)

        # print url
        request = urllib2.Request(url)

        # Make the HTTP request.
        response = urllib2.urlopen(request)
        assert response.code == 200

        # Use the json module to load CKAN's response into a dictionary.
        response_dict = json.loads(response.read())
        return response_dict

    def parse_xml(self, path):
        # get xml file
        tree = et.parse(path)
        self.data['spatial_points'] = []

        for el in tree.iter():
            if '}' in el.tag:
                el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
                # print el.tag

        root = tree.find('isebel')
        self.get_element(root)

        index_list = list()
        for index in root.iter('index'):
            index_list.append(index.text)
        self.data['index'] = ','.join(index_list)

        keyword_list = list()
        for keyword in root.iter('keyWord'):
            keyword_list.append(keyword.text)

        self.data['keyword'] = '; '.join(keyword_list)

        for spatial_point in root.iter('placeOfNarration') or root.iter('placeOfMentioned'):
            spatial_points = self.forward_geocoding(spatial_point.text, 'pk.eyJ1IjoidmljZGluZy1kaSIsImEiOiJjamtjajVod28waHN5M3FxZmw4YTMwdWJxIn0.8thy3AiluSOpJrukB8p0xQ')
            # pprint(spatial_points['features'][0]['center'])
            try:
                self.data['spatial_points'].append(spatial_points['features'][0]['center'])
            except Exception as e:
                print 'No spatial points'
        # pprint(self.data['spatial_points'])
        return self.data


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
            return response_dict

    return None


def create_package(org, f, apikey):
    isebel_list = ['text', 'url', 'datePublished', 'narrator', 'placeOfNarration', 'placeMentioned']
    data = XML().parse_xml(f)
    data['md5'] = md5(f)

    # check if dataset exists and not modified
    response_dict = get_package_by_id(data['name'], apikey=apikey)
    old_md5 = ''
    if response_dict:
        print 'Existing data set, checking MD5...'
        for extra in response_dict['result']['extras']:
            if extra['key'] == 'MD5':
                old_md5 = extra['value']
        if old_md5 == data['md5']:
            print 'MD5 identical, skipping!'
            return True
        else:
            remove_all_created_package(response_dict, apikey)
            print 'MD5 different, updating!'
    else:
        print 'New dataset, adding new!'

    # Create dataset
    # Put the details of the dataset we're going to create into a dict.
    dataset_dict = {
        'name': data['identifier'].lower(),
        'notes': data['text'],
        'owner_org': org,
        'extras': []
    }

    try:
        for i in isebel_list:
            if i == 'url':
                dataset_dict['extras'].append(
                    {
                        'key': 'data_url',
                        'value': data[i]
                    }
                )
            elif i == 'text':
                pass
            else:
                dataset_dict['extras'].append(
                    {
                        'key': i,
                        'value': data[i]
                    }
                )
    except Exception as e:
        print e.message
        print i

    # dataset_dict['extras'].append(
    #     {
    #         'key': 'index',
    #         'value': data['index']
    #     }
    # )

    dataset_dict['extras'].append(
        {
            'key': 'MD5',
            'value': data['md5']
        }
    )

    dataset_dict['extras'].append(
        {
            'key': 'da_keyword',
            'value': data['keyword']
        }
    )

    spatial_points = data['spatial_points']

    if len(spatial_points) > 1:
        print(spatial_points)
        dataset_dict['extras'].append(
            {
                'key': 'spatial',
                'value': json.dumps(
                    {
                        'type': 'MultiPoint',
                        'coordinates': spatial_points
                    }
                )
            }
        )
    elif len(spatial_points) == 1:
        print spatial_points[0]
        dataset_dict['extras'].append(
            {
                'key': 'spatial',
                'value': json.dumps(
                    {
                        'type': 'Point',
                        'coordinates': spatial_points[0]
                    }
                )
            }
        )

    # exit(dataset_dict['extras'])

    # Use the json module to dump the dictionary to a string for posting.
    data_string = urllib.quote(json.dumps(dataset_dict))

    # We'll use the package_create function to create a new dataset.
    request = urllib2.Request(
        'http://ckan:5000/api/3/action/package_create')

    # Creating a dataset requires an authorization header.
    request.add_header('Authorization', apikey)

    # Make the HTTP request.
    response = urllib2.urlopen(request, data_string)
    assert response.code == 200

    # Use the json module to load CKAN's response into a dictionary.
    response_dict = json.loads(response.read())
    assert response_dict['success'] is True

    # package_create returns the created package as its result.
    created_package = response_dict['result']
    # pprint.pprint(created_package)
    return True


def __main__():
    start = time.time()
    print 'start'
    apikey = "e6c1b9c8-3a5f-44b9-9b12-b9f8f8c4ca36"
    wd = '/var/harvester/oai-isebel/isebel_ucla'
    org = 'isebel_ucla'
    debug = False
    qty = 100

    # Get current dataset names
    # print 'before getting created package'
    # created_package = get_created_package(org, apikey)
    # print 'after getting created package'
    # Remove all the datasets
    # remove_all_created_package(created_package, apikey)

    created_package = get_created_package(org, apikey)
    while len(created_package) > 0 and debug:
        created_package = get_created_package(org, apikey)
        remove_all_created_package(created_package, apikey)

        print 'removing dataset'
    else:
        print 'removed dataset'

    files = [join(wd, f) for f in sorted(listdir(wd)) if f.endswith('.xml') and isfile(join(wd, f))]
    print 'get file lists'
    # counter = 0
    # for f in files:
    #     if counter > qty - 1 and debug:
    #         break
    #     counter += 1
    #     print f
    #     create_package(org, f, apikey=apikey)


    # TODO: add md5 checkup and partial updates
    counter = 0

    for f in files:
        print '### start with file: %s ###' % f
        result = None
        # try:
        result = create_package(org, f, apikey=apikey)
        # except Exception as e:
        #     print e.message
        #     print 'error processing file!'
        # print result
        if counter > qty - 1 and debug:
            break
        if result:
            counter += 1
        print '### end with file: %s ###' % f
    end = time.time()
    elapsed = end - start
    print '#### Overview ###'
    print '#### Start at: %s' % start
    print '#### Ends at: %s' % end
    print '#### Time elapsed: %s' % elapsed
    # TODO: end

__main__()
