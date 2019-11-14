# -*- coding: utf-8 -*-
import urllib2
import json
import xml.etree.ElementTree as et
from os import listdir
from os.path import isfile, join
import time
from pprint import pprint
from xmljson import badgerfish as bf
import re
import sys

import import_xml_to_ckan_util as importlib

story_fields = ['identifier', 'title', 'type', 'contents', 'places', 'persons', 'events', 'keywords', ]


class XML:
    def __init__(self):
        pass

    data = dict()

    def get_element(self, tree, isebel_list=None):
        if isebel_list is None:
            isebel_list = story_fields
        for i in isebel_list:
            self.data[i] = tree.find(i) if tree.find(i) is not None else None

    @staticmethod
    def parse_xml(path):
        # get xml file
        try:
            tree = et.parse(path)
        except Exception as e:
            tree = None
            print('error parsing XML file!')
            exit(e.message)

        for el in tree.iter():
            if '}' in el.tag:
                el.tag = el.tag.split('}', 1)[1]  # strip all namespaces

        root = tree.getroot()
        for el in root:
            if '}' in el.tag:
                el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
                print(el.tag)

        # self.data['id'] = root.attrib['{http://www.w3.org/XML/1998/namespace}id']
        return root


def load_dict_from_xml(xml, path):
    # converting XML data to json
    data = bf.data(xml)
    # converting json to dict and clean out NS from key names
    data = json.loads(json.dumps(data).replace('{http://www.w3.org/XML/1998/namespace}', '').replace(
        '{http://www.w3.org/2001/XMLSchema-instance}', ''))
    # get story from dict
    story = data.get('story', None)

    if story is not None:
        # add md5 of the current file to data
        story['md5'] = importlib.md5(path)
        return story

    return None


def create_package(org, f, apikey):
    raw_xml = ''
    with open(f, 'r') as fh:
        raw_xml = fh.readlines()
    raw_xml = ''.join(raw_xml)

    # getting xml data
    xml_data = XML().parse_xml(f)
    # getting dict from xml data
    story_dict = load_dict_from_xml(xml_data, f)
    # print('story_dict: ', json.dumps(story_dict))

    # check if dataset exists in and original XML file not modified using story id
    story_id = story_dict.get('@id', None)
    response_dict = importlib.get_package_by_name(story_id, apikey=apikey)
    # insert/update/skip package creation based on MD5 of XML file
    old_md5 = ''
    if response_dict:
        print('Existing data set {}, checking MD5...'.format(story_id))
        for extra in response_dict['result']['extras']:
            if extra['key'] == 'MD5':
                old_md5 = extra['value']
        if old_md5 == story_dict['md5']:
            print('MD5 identical, skipping!')
            return True
        else:
            importlib.remove_all_created_package(response_dict, apikey)
            print('MD5 different, updating!')
    else:
        print('New dataset, adding new!')

    # Create dataset
    # Put the details of the dataset we're going to create into a dict.
    # print('taleTypes: ', story_dict.get('taleTypes').get('taleType'))
    # print(type(story_dict.get('taleTypes').get('taleType')))
    pattern = re.compile('[^a-zA-Z0-9_-]+')
    dataset_dict = {
        'name': pattern.sub('-', story_dict.get('identifier').get('$').lower()),
        # pattern.sub('_', story_dict.get('@id').lower()),
        'title': story_dict.get('identifier').get('$'),  # story_dict.get('@id'),
        'notes': story_dict.get('contents').get('content').get('$') if isinstance(
            story_dict.get('contents').get('content'), dict) else story_dict.get('contents').get('content')[0].get('$'),
        'url': str(story_dict.get('purl').get('$')),
        # 'type': story_dict.get('type').get('$'),
        'owner_org': org,
        'extras': [
            {
                'key': 'MD5',
                'value': story_dict.get('md5')
            },
            {
                'key': 'raw_xml',
                'value': raw_xml
            },
            {
                'key': 'identifier',
                'value': story_dict.get('identifier').get('$')
            },
            {
                'key': 'Type',
                'value': story_dict.get('type').get('$') if story_dict.get('type') else None
            },
        ]
    }
    # exit(dataset_dict)
    # add keywords
    if story_dict.get('keywords') and story_dict.get('keywords').get('keyword'):
        if isinstance(story_dict.get('keywords').get('keyword'), list):
            keywords_list = list()
            for i in story_dict.get('keywords').get('keyword'):
                if not isinstance(i.get('$'), bool) and not isinstance(i.get('$'), int):
                    keywords_list.append(i.get('$'))
                else:
                    keywords_list.append(str(i.get('$')))

            dataset_dict['extras'].append({
                'key': '%s_keyword' % story_dict.get('@lang'),
                'value': '; '.join([i for i in keywords_list])
            })
        else:
            keywords_list = story_dict.get('keywords').get('keyword').get('$')
            if isinstance(keywords_list, bool) or isinstance(keywords_list, int):
                keywords_list = str(keywords_list)
            dataset_dict['extras'].append({
                'key': '%s_keyword' % story_dict.get('@lang'),
                'value': keywords_list
            })

    # add taleTypes
    taleTypes = story_dict.get('taleTypes').get('taleType') if story_dict.get('taleTypes') is not None else None
    if isinstance(taleTypes, dict):
        dataset_dict['extras'].append(
            {'key': 'Tale Type', 'value': '%s: %s' % (taleTypes.get('@number'), taleTypes.get('@title'))})
        dataset_dict['extras'].append(
            {'key': taleTypes.get('@number'), 'value': taleTypes.get('@title')})
    elif isinstance(taleTypes, list):
        value = '; '.join(['%s: %s' % (taleType.get('@number'), taleType.get('@title')) for taleType in taleTypes])
        dataset_dict['extras'].append({'key': 'Tale Type', 'value': value})
        for taleType in taleTypes:
            dataset_dict['extras'].append(
                {'key': taleType.get('@number'), 'value': taleType.get('@title')})

    # add events
    events = story_dict.get('events').get('event') if story_dict.get('events') is not None else None
    if isinstance(events, dict):
        try:
            if events.get('role', None) is not None and events.get('date', None) is not None:
                dataset_dict['extras'].append(
                    {'key': events.get('role').get('$').capitalize(), 'value': events.get('date').get('$')})
        except Exception as ex:
            print(events)
            exit(ex.message)
    elif isinstance(events, list):
        for event in events:
            dataset_dict['extras'].append(
                {'key': event.get('role').get('$').capitalize(), 'value': event.get('date').get('$')})

    # add contents
    contents = story_dict.get('contents').get('content') if story_dict.get('contents') is not None else None
    if isinstance(contents, dict):
        dataset_dict['extras'].append(
            {'key': contents.get('@lang'), 'value': contents.get('$')})
    elif isinstance(contents, list):
        for content in contents:
            dataset_dict['extras'].append(
                {'key': content.get('@lang'), 'value': content.get('$')})

    # add persons
    persons = story_dict.get('persons').get('person') if story_dict.get('persons') is not None else None
    if isinstance(persons, dict):
        importlib.process_persons(persons, dataset_dict)
    elif isinstance(persons, list):
        for person in persons:
            importlib.process_persons(person, dataset_dict)

    # add places
    places = story_dict.get('places').get('place') if story_dict.get('places') is not None else None
    if isinstance(places, dict):
        if places.get('point', None) is not None:
            dataset_dict['extras'].append(
                {'key': places.get('title').get('$') if places.get('title') is not None else places.get('@id'),
                 'value': '%s, %s' % (
                     places.get('point').get('pointLongitude').get('$'),
                     places.get('point').get('pointLatitude').get('$'))})

            dataset_dict['extras'].append(
                {'key': 'spatial',
                 'value': json.dumps({'type': 'Point',
                                      'coordinates': [float(places.get('point').get('pointLongitude').get('$')),
                                                      float(places.get('point').get('pointLatitude').get('$'))]})})
        else:
            dataset_dict['extras'].append(
                {'key': places.get('title').get('$') if places.get('title') is not None else places.get('@id'),
                 'value': ''})

    elif isinstance(places, list):
        geopoints = list()
        existing_keys = list()
        for place in places:
            if isinstance(place.get('title'), list):
                key = [i for i in place.get('title')]
            elif isinstance(place.get('title'), dict):
                key = place.get('title').get('$') if place.get('title', None) is not None else place.get('@id')

            if place.get('point', False) and place.get('point').get('pointLongitude',
                                                                    False) and key not in existing_keys:
                dataset_dict['extras'].append(
                    {'key': key,
                     'value': '%s, %s' % (place.get('point').get('pointLongitude').get('$'),
                                          place.get('point').get('pointLatitude').get('$'))})
                geopoints.append([float(place.get('point').get('pointLongitude').get('$')),
                                  float(place.get('point').get('pointLatitude').get('$'))])
                existing_keys.append(key)
        dataset_dict['extras'].append(
            {'key': 'spatial',
             'value': json.dumps({'type': 'MultiPoint',
                                  'coordinates': geopoints})})

    # Use the json module to dump the dictionary to a string for posting
    data_string = urllib2.quote(json.dumps(dataset_dict))

    # use the package_create function to create a new dataset
    request = urllib2.Request(
        'http://ckan:5000/api/3/action/package_create')

    # add authorization header
    request.add_header('Authorization', apikey)

    # Make the HTTP request.
    try:
        response = urllib2.urlopen(request, data_string)
        # assert response.code == 200
    except urllib2.HTTPError as ex:
        pprint(dataset_dict)
        print(ex)
        return False

    # Use the json module to load CKAN's response into a dictionary.
    response_dict = json.loads(response.read())
    assert response_dict.get('success', False) is True

    # package_create returns the created package as its result.
    # created_package = response_dict['result']
    # pprint(created_package)
    return True


def __main__():
    start = time.time()

    print('start')
    args = None
    try:
        args = sys.argv[1]
    except IndexError:
        exit('organization is required on the command line')

    try:
        clean = sys.argv[2]
    except IndexError:
        clean = False

    if args in ('meertens', 'verhalenbank'):
        org = 'meertens'
        wd = '/var/harvester/oai-isebel/isebel_verhalenbank'
    elif args == 'ucla':
        org = 'ucla'
        wd = '/var/harvester/oai-isebel/isebel_ucla'
    elif args in ('wossidia', 'rostock'):
        org = 'wossidia'
        wd = '/var/harvester/oai-isebel/isebel_rostock'
    else:
        raise Exception('Invalid organization')

    apikey = importlib.apikey
    debug = importlib.debug
    qty = importlib.qty

    # if not org Create it
    if not importlib.org_exists(org):
        print('organization [%s] does not exist. Creating!' % org)
        if importlib.create_org(org):
            print('organization [%s] created!' % org)
        else:
            exit('organization [%s] cannot be created!' % org)
    else:
        print('organization [%s] already exists.' % org)

    # created_package = get_all_created_package(apikey)
    created_package = importlib.get_created_package(org, apikey)
    print('From outside loop: %s created packages; debug is: %s; clean is: %s' % (len(created_package), debug, clean))
    while len(created_package) > 0 and (debug or clean):
        print('From inside loop: %s created packages; debug is: %s; clean is: %s' % (
            len(created_package), debug, clean))
        created_package = importlib.get_created_package(org, apikey)
        # created_package = get_all_created_package(apikey)
        importlib.remove_all_created_package(created_package, apikey)
        if clean:
            print('cleaning old datasets')
        else:
            print('removing old dataset')
    else:
        print('removed dataset')

    files = [join(wd, f) for f in sorted(listdir(wd)) if f.endswith('.xml') and isfile(join(wd, f))]
    print('get file lists')
    counter = 0

    for f in files:
        print('### start with file: %s ###' % f)
        result = create_package(org, f, apikey=apikey)

        if counter > qty - 1 and debug:
            break
        if result:
            counter += 1
        print('### end with file: %s ###' % f)
    end = time.time()
    elapsed = end - start
    print('#### Overview ###')
    print('#### Start at: %s' % start)
    print('#### Ends at: %s' % end)
    print('#### Time elapsed: %s' % elapsed)

    if importlib.set_title_homepage_style():
        print('#### Website title and home page style set successfully')
    else:
        print('#### Website title and home page style set failed')


__main__()
