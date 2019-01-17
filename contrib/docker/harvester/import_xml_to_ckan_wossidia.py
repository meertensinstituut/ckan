# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import urllib2
import json
import xml.etree.ElementTree as et
from os import listdir
from os.path import isfile, join

import import_xml_to_ckan_util as importlib

class XML():
    isebel_list = ['identifier', 'title', 'subtitle']
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
        self.get_element(root)

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
            # print content.attrib['{http://www.w3.org/XML/1998/namespace}lang']
            # print content.text.encode('utf-8')
        self.data['content'] = content_dict
        # exit(self.data)
        return self.data


def create_package(org, f, apikey):
    isebel_list = ['identifier', 'title', 'subtitle']
    data = XML().parse_xml(f)
    data['md5'] = importlib.md5(f)

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
        print i

    dataset_dict['extras'].append(
        {
            'key': 'MD5',
            'value': data['md5']
        }
    )

    try:
        for (k, v) in data['content'].items():
            # print k
            # print v
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
    # pprint.pprint(created_package)


def __main__():
    print 'start'
    apikey = importlib.apikey
    wd = '/var/harvester/oai-isebel/isebel_rostock'
    org = 'isebel_wossidia'
    debug = False
    qty = 100

    created_package = importlib.get_created_package(org, apikey)
    while len(created_package) > 0 and debug:
        created_package = importlib.get_created_package(org, apikey)
        importlib.remove_all_created_package(created_package, apikey)

        print 'removing dataset'
    else:
        print 'removed dataset'

    files = [join(wd, f) for f in sorted(listdir(wd)) if f.endswith('.xml') and isfile(join(wd, f))]
    print 'get file lists'
    counter = 0
    for f in files:
        if counter > qty - 1 and debug:
            break
        counter += 1
        print f
        create_package(org, f, apikey=apikey)


__main__()
