# -*- coding: utf-8 -*-
import urllib2
import json
import xml.etree.ElementTree as et
from collections import OrderedDict
from os import listdir
from os.path import isfile, join
import time
from pprint import pprint
from xmljson import badgerfish as bf

import import_xml_to_ckan_util as importlib

story_fields = ['identifier', 'title', 'type', 'contents', 'places', 'persons', 'events', 'keywords', ]


class XML:
    data = dict()

    def get_element(self, tree, isebel_list=story_fields):
        for i in isebel_list:
            self.data[i] = tree.find(i) if tree.find(i) is not None else None

    def parse_xml(self, path):
        # get xml file
        try:
            tree = et.parse(path)
        except Exception as e:
            print('error parsing XML file!')
            print(e.message)

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
        print('Existing data set, checking MD5...')
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

    dataset_dict = {
        'name': story_dict.get('@id'),
        'title': story_dict.get('@id'),
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
                'key': 'identifier',
                'value': story_dict.get('identifier').get('$')
            },
            {
                'key': 'Type',
                'value': story_dict.get('type').get('$')
            },
            {
                'key': '%s_keyword' % story_dict.get('@lang'),
                'value': '; '.join([i.get('$') for i in story_dict.get('keywords').get('keyword')])
            },

            # {
            #     'key': 'date',
            #     'value': story_dict['date']
            # },
        ]
    }

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
        dataset_dict['extras'].append(
            {'key': events.get('role').get('$').capitalize(), 'value': events.get('date').get('$')})
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
        dataset_dict['extras'].append(
            {'key': persons.get('role').get('$'), 'value': persons.get('name').get('$')})
        dataset_dict['extras'].append(
            {'key': persons.get('role').get('$') + ' gender', 'value': persons.get('gender').get('$')})
    elif isinstance(persons, list):
        for person in persons:
            dataset_dict['extras'].append(
                {'key': person.get('role').get('$'), 'value': person.get('name').get('$')})
            dataset_dict['extras'].append(
                {'key': person.get('role').get('$') + ' gender', 'value': person.get('gender').get('$')})

    # add places
    places = story_dict.get('places').get('place') if story_dict.get('places') is not None else None
    if isinstance(places, dict):
        dataset_dict['extras'].append(
            {'key': places.get('title').get('$') if places.get('title') is not None else places.get('@id'),
             'value': '%s, %s' % (places.get('point').get('pointLongitude').get('$'), places.get('point').get('pointLatitude').get('$'))})
        dataset_dict['extras'].append(
            {'key': 'spatial',
             'value': json.dumps({'type': 'Point',
                                  'coordinates': [float(places.get('point').get('pointLongitude').get('$')),
                                                  float(places.get('point').get('pointLatitude').get('$'))]})})
    elif isinstance(places, list):
        geopoints = list()
        existing_keys = list()
        for place in places:
            key = place.get('title').get('$') if place.get('title') is not None else place.get('@id')
            if key not in existing_keys:
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

    pprint(story_dict)
    exit()
    # spatial_points = data['spatial_points']
    #
    # for geo_location in data['location']:
    #     for k, v in geo_location.items():
    #         dataset_dict['extras'].append(
    #             {
    #                 'key': k,
    #                 'value': v
    #             }
    #         )

    # if len(spatial_points) > 1:
    #     print('MultiPoint: %s' % spatial_points)
    #     dataset_dict['extras'].append(
    #         {
    #             'key': 'spatial',
    #             'value': json.dumps(
    #                 {
    #                     'type': 'MultiPoint',
    #                     'coordinates': spatial_points
    #                 }
    #             )
    #         }
    #     )
    # elif len(spatial_points) == 1:
    #     print('Point: %s' % spatial_points[0])
    #     dataset_dict['extras'].append(
    #         {
    #             'key': 'spatial',
    #             'value': json.dumps(
    #                 {
    #                     'type': 'Point',
    #                     'coordinates': spatial_points[0]
    #                 }
    #             )
    #         }
    #     )
    #
    # for person in data['person']:
    #     for k, v in person.items():
    #         dataset_dict['extras'].append(
    #             {
    #                 'key': k,
    #                 'value': v
    #             }
    #         )
    # exit(dataset_dict['extras'])

    # Use the json module to dump the dictionary to a string for posting.
    # data_string = urllib2.quote(json.dumps(dataset_dict))
    data_string = urllib2.quote(json.dumps(dataset_dict))

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
    # pprint(created_package)
    return True


def __main__():
    start = time.time()
    print('start')
    org = 'meertens'

    # if not org Create it
    if not importlib.org_exists(org):
        print('organization [%s] does not exist. Creating!' % org)
        if importlib.create_org(org):
            print('organization [%s] created!' % org)
        else:
            exit('organization [%s] cannot be created!' % org)
    else:
        print('organization [%s] already exists.' % org)

    apikey = importlib.apikey
    wd = '/var/harvester/oai-isebel/isebel_verhalenbank'
    debug = importlib.debug
    qty = importlib.qty

    # Get current dataset names
    # print 'before getting created package'
    # created_package = get_created_package(org, apikey)
    # print 'after getting created package'
    # Remove all the datasets
    # remove_all_created_package(created_package, apikey)

    # created_package = get_all_created_package(apikey)
    created_package = importlib.get_created_package(org, apikey)
    while len(created_package) > 0 and debug:
        created_package = importlib.get_created_package(org, apikey)
        # created_package = get_all_created_package(apikey)
        importlib.remove_all_created_package(created_package, apikey)

        print('removing dataset')
    else:
        print('removed dataset')

    files = [join(wd, f) for f in sorted(listdir(wd)) if f.endswith('.xml') and isfile(join(wd, f))]
    print('get file lists')
    counter = 0

    for f in files:
        print('### start with file: %s ###' % f)
        result = None
        # try:
        result = create_package(org, f, apikey=apikey)
        # except Exception as e:
        #     print(e.message)
        #     print('error processing file!')
        # print result
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
