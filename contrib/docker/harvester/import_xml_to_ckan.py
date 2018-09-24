# -*- coding: utf-8 -*-
import urllib2
import urllib
import json
import requests
import xml.etree.ElementTree as et
import hashlib
import datetime
from os import listdir
from os.path import isfile, join


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
        requests.post('http://ckan:5000/api/3/action/package_delete',
                      data=dataset_dict,
                      headers={"X-CKAN-API-Key": apikey})
        # purge dataset
        requests.post('http://ckan:5000/api/3/action/dataset_purge',
                      data=dataset_dict,
                      headers={"X-CKAN-API-Key": apikey})


class XML():
    isebel_list = ['title', 'identifier', 'content', 'ref', 'type']
    data = dict()

    def get_element(self, tree, isebel_list = isebel_list):
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
        self.data['story'] = root.attrib['{http://www.w3.org/XML/1998/namespace}id']

        self.get_element(tree)
        if self.data['story'] and not self.data['title']:
            self.data['name'] = self.data['story']
        else:
            self.data['name'] = '%s_%s' % self.data['story'], self.data['title'].lower()

        # get location data
        self.data['location'] = []
        self.data['spatial_points'] = []
        if root.find('geoLocations') is not None:

            self.data['location_names'] = list()
            self.data['location_geopoints'] = list()
            for geo_location in root.find('geoLocations'):
                self.data['location_names'].append(geo_location.find('geoLocationPlace').text if geo_location.find('geoLocationPlace') is not None else '')
                self.data['location_geopoints'].append([float(geo_location.find('geoLocationPoint').find('pointLongitude').text), float(geo_location.find('geoLocationPoint').find('pointLatitude').text)])
                location_id = geo_location.attrib['{http://www.w3.org/XML/1998/namespace}id']

                self.data['location'].append(
                    {
                        'location_name_%s' % location_id: geo_location.find('geoLocationPlace').text if geo_location.find('geoLocationPlace') is not None else '',
                        'location_id_%s' % location_id: location_id,
                        'location_geopoint_%s' % location_id: [geo_location.find('geoLocationPoint').find('pointLongitude').text, geo_location.find('geoLocationPoint').find('pointLatitude').text] if geo_location.find('geoLocationPoint').find('pointLatitude') is not None else None
                    }
                )

                # get geolocation in geojson (acutally as array, will json.dumps to json
                if geo_location.find('geoLocationPoint').find('pointLatitude').text is not None:
                    self.data['spatial_points'].append([float(geo_location.find('geoLocationPoint').find('pointLongitude').text), float(geo_location.find('geoLocationPoint').find('pointLatitude').text)])

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

        # get date
        if root.find('date') is not None:
            if isdate(root.find('date').text[:10]):
                self.data['date'] = root.find('date').text[:10]
            elif isdate(root.find('date').text[:8], '%y-%m-%d'):
                self.data['date'] = '19%s' % root.find('date').text[:8]
            else:
                self.data['date'] = None
        else:
            self.data['date'] = None

        # get keyword
        keyword_list = list()
        # if root.find('keyword') is not None:
        for keyword in root.iter('keyword'):
            keyword_list.append(keyword.text)

        self.data['keyword'] = '; '.join(keyword_list)

        return self.data


def create_package(org, f, apikey):
    data = XML().parse_xml(f)
    data['md5'] = md5(f)

    # Create dataset
    # Put the details of the dataset we're going to create into a dict.
    dataset_dict = {
        'name': data['name'],
        'notes': data['content'],
        'owner_org': org,
        'extras': [
            {
                'key': 'Reference',
                'value': data['ref']
            },
            {
                'key': 'MD5',
                'value': data['md5']
            },
            {
                'key': 'identifier',
                'value': data['identifier']
            },
            {
                'key': 'dc_type',
                'value': data['type']
            },
            {
                'key': 'nl_keyword',
                'value': data['keyword']
            },
            {
                'key': 'date',
                'value': data['date']
            },
            # {
            #     'key': 'spatial',
            #     'value': json.dumps({
            #         "type": "Point",
            #         "coordinates": [-3.145,53.078]
            #     })
            # },
        ]
    }

    # exit(dataset_dict)
    spatial_points = data['spatial_points']

    for geo_location in data['location']:
        for k, v in geo_location.items():
            dataset_dict['extras'].append(
                {
                    'key': k,
                    'value': v
                }
            )

            # if 'location_name' in k:
            #     try:
            #         dataset_dict['extras'].append(
            #             {
            #                 'key': 'placeOfNarration',
            #                 'value': v
            #             }
            #         )
            #     except:
            #         pass

    print data['location_names']
    print data['location_geopoints']
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

    for person in data['person']:
        for k, v in person.items():
            dataset_dict['extras'].append(
                {
                    'key': k,
                    'value': v
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


def __main__():
    print 'start'
    apikey = "5f38155e-1e79-4ac6-889f-ecea89991375"
    wd = '/var/harvester/oai-isebel/isebel_verhalenbank'
    org = 'isebel_verhalenbank'
    debug = True
    qty = 100

    # Get current dataset names
    print 'before getting created package'
    created_package = get_created_package(org, apikey)
    print 'after getting created package'
    # Remove all the datasets
    remove_all_created_package(created_package, apikey)

    created_package = get_all_created_package(apikey)
    while len(created_package) > 0:
        # created_package = get_created_package(org, apikey)
        created_package = get_all_created_package(apikey)
        remove_all_created_package(created_package, apikey)

        print 'removing dataset'
    else:
        print 'removed dataset'

    files = [join(wd, f) for f in listdir(wd) if isfile(join(wd, f))]
    print 'get file lists'
    counter = 0
    for f in files:
        if counter > qty - 1 and debug:
            break
        counter += 1
        print f
        create_package(org, f, apikey=apikey)


__main__()
