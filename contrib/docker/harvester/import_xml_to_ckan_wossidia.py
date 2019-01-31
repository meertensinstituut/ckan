# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import time
import urllib2
import json
import xml.etree.ElementTree as et
from os import listdir
from os.path import isfile, join
from pprint import pprint

import import_xml_to_ckan_util as importlib

isebel_list = ['identifier', 'title']


class XML:
    data = dict()

    def __init__(self):
        pass

    def get_element(self, tree, isebel_list=isebel_list):
        for i in isebel_list:
            tmp = tree.find(i)
            self.data[i] = tmp.text if tmp is not None else None

    def parse_xml(self, path):
        # get xml file
        tree = et.parse(path)

        for el in tree.iter():
            if '}' in el.tag:
                el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
                # print el.tag

        root = tree.getroot()
        self.get_element(root)

        self.data['name'] = "".join([c if c.isalnum() else "-" for c in str(self.data['identifier'])])

        content_dict = dict()
        for content in root.iter('content'):
            try:
                lang = content.attrib['{http://www.w3.org/XML/1998/namespace}lang']
            except Exception as e:
                lang = 'deu'

            if lang not in content_dict.keys():
                content_dict[lang] = content.text.encode('utf-8')

            if lang == 'deu':
                self.data['text'] = content.text.encode('utf-8')

        self.data['content'] = content_dict

        keyword_list = list()
        for keyword in root.iter('keyword'):
            keyword_list.append(keyword.text)

        self.data['keyword'] = '; '.join(keyword_list)

        # get location data
        self.data['location'] = []
        self.data['spatial_points'] = []
        if root.find('geoLocations') is not None:
            self.data['location_names'] = list()
            self.data['location_geopoints'] = list()

            for geo_location in root.find('geoLocations'):
                self.data['location_names'].append(geo_location.find('geoLocationPlace').text if geo_location.find(
                    'geoLocationPlace') is not None else '')

                if geo_location.find('geoLocationPoint').find('pointLongitude').text is not None and geo_location.find(
                        'geoLocationPoint').find('pointLatitude').text is not None:

                    self.data['location_geopoints'].append(
                        [float(geo_location.find('geoLocationPoint').find('pointLongitude').text),
                         float(geo_location.find('geoLocationPoint').find('pointLatitude').text)])

                    self.data['spatial_points'].append(
                        [float(geo_location.find('geoLocationPoint').find('pointLongitude').text),
                         float(geo_location.find('geoLocationPoint').find('pointLatitude').text)])

                location_id = geo_location.attrib['{http://www.w3.org/XML/1998/namespace}id']

                self.data['location'].append(
                    {
                        'location_name_%s' % location_id: geo_location.find(
                            'geoLocationPlace').text if geo_location.find('geoLocationPlace') is not None else '',
                        'location_id_%s' % location_id: location_id,
                        'location_geopoint_%s' % location_id: [
                            geo_location.find('geoLocationPoint').find('pointLongitude').text,
                            geo_location.find('geoLocationPoint').find('pointLatitude').text] if geo_location.find(
                            'geoLocationPoint').find('pointLatitude') is not None else None
                    }
                )

        # get person data
        self.data['person'] = []
        person_type = dict()
        if root.find('person') is not None:
            for person in root.iter('person'):
                if person.find('role').text not in person_type.keys():
                    person_type[person.find('role').text] = list()
                person_type[person.find('role').text].append(person.find('contributor').text)

            for k, v in person_type.iteritems():
                self.data['person'].append(
                    {
                        k: ', '.join(v)
                    }
                )

        # get keyword
        keyword_list = list()
        # if root.find('keyword') is not None:
        for keyword in root.iter('keyword'):
            keyword_list.append(keyword.text)

        self.data['keyword'] = '; '.join(keyword_list)

        # exit(self.data)
        return self.data


def create_package(org, f, apikey):
    data = XML().parse_xml(f)
    data['md5'] = importlib.md5(f)

    # check if dataset exists and not modified
    response_dict = importlib.get_package_by_id(data['name'], apikey=apikey)
    pprint(data)

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
            importlib.remove_all_created_package(response_dict, apikey)
            print 'MD5 different, updating!'
    else:
        print 'New dataset, adding new!'

    # Create dataset
    # Put the details of the dataset we're going to create into a dict.
    dataset_dict = {
        'name': "".join([c if c.isalnum() else "-" for c in str(data['identifier'])]),
        'notes': data['text'],
        'owner_org': org,
        'title': data['title'],
        'extras': []
    }

    try:
        for i in isebel_list:
            if i == 'title':
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

    dataset_dict['extras'].append(
        {
            'key': 'MD5',
            'value': data['md5']
        }
    )

    for person in data['person']:
        for k, v in person.items():
            dataset_dict['extras'].append(
                {
                    'key': k,
                    'value': v
                }
            )

    spatial_points = data['spatial_points']

    for geo_location in data['location']:
        for k, v in geo_location.items():
            dataset_dict['extras'].append(
                {
                    'key': k,
                    'value': v
                }
            )

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

    # dataset_dict['extras'].append(
    #     {
    #         'key': 'de_keyword',
    #         'value': data['keyword']
    #     }
    # )

    try:
        for (k, v) in data['content'].items():
            if not k == 'deu':
                dataset_dict['extras'].append(
                    {
                        'key': k,
                        'value': v
                    }
                )
    except Exception as e:
        print e.message

    # Use the json module to dump the dictionary to a string for posting.
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
    pprint(created_package)
    return True


def __main__():
    start = time.time()
    print 'start'
    org = 'wossidia'

    # if not org Create it
    if not importlib.org_exists(org):
        print 'organization [%s] does not exist. Creating!' % org
        if importlib.create_org(org):
            print 'organization [%s] created!' % org
        else:
            exit('organization [%s] cannot be created!' % org)
    else:
        print 'organization [%s] already exists.' % org

    apikey = importlib.apikey
    wd = '/var/harvester/oai-isebel/isebel_rostock'
    debug = importlib.debug
    qty = importlib.qty

    print('getting created packages from current organization!')
    created_package = importlib.get_created_package(org, apikey)
    print('removing all the data sets from current organization')
    while len(created_package) > 0 and debug:
        created_package = importlib.get_created_package(org, apikey)
        importlib.remove_all_created_package(created_package, apikey)
        print 'removing dataset %s' % created_package
    else:
        print 'removed dataset'

    print 'geting file lists'
    files = [join(wd, f) for f in sorted(listdir(wd)) if f.endswith('.xml') and isfile(join(wd, f))]

    counter = 0

    for f in files:
        print '### start with file: %s ###' % f
        print '### counter: %s' % counter
        counter += 1
        result = create_package(org, f, apikey=apikey)

        # print result
        if counter > qty - 1 and debug:
            break
        print '### end with file: %s ###' % f
    end = time.time()
    elapsed = end - start
    print '#### Overview ###'
    print '#### Start at: %s' % start
    print '#### Ends at: %s' % end
    print '#### Time elapsed: %s' % elapsed


__main__()
