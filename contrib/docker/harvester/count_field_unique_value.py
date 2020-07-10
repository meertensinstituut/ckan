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

        # self.data['id'] = root.attrib['{http://www.w3.org/XML/1998/namespace}id']
        return root


def load_story_from_xml_as_dict(xml):
    # converting XML data to json
    data = bf.data(xml)
    # converting json to dict and clean out NS from key names
    data = json.loads(json.dumps(data).replace('{http://www.w3.org/XML/1998/namespace}', '').replace(
        '{http://www.w3.org/2001/XMLSchema-instance}', ''))
    # get story from dict
    story = data.get('story', None)
    return story


def get_story_from_xml_file(f):
    # getting xml data
    xml_data = XML().parse_xml(f)
    # getting dict from xml data
    story_dict = load_story_from_xml_as_dict(xml_data)
    return story_dict


def get_unique_field_value_as_set(story_dict, field_name='keywords'):
    if story_dict.get('keywords', None) and story_dict.get('keywords').get('keyword', None):
        # print(story_dict.get('keywords', None))
        keywords_list = list()
        if isinstance(story_dict.get('keywords').get('keyword'), list):
            for i in story_dict.get('keywords').get('keyword'):
                # if not isinstance(i.get('$'), bool) and not isinstance(i.get('$'), int):
                #     keywords_list.append(i.get('$'))
                # else:
                keywords_list.append(i.get('$'))
        else:
            keyword = story_dict.get('keywords').get('keyword').get('$')
            # if isinstance(keywords_list, bool) or isinstance(keywords_list, int):
            keywords_list.append(keyword)

        return set(keywords_list)
    return None


def __main__():
    start = time.time()

    print('start')
    # init the config
    importlib.init()

    args = None
    try:
        args = sys.argv[1]
    except IndexError:
        exit('organization is required on the command line')

    if args in ('meertens', 'verhalenbank'):
        org = 'meertens'
    elif args == 'ucla':
        org = 'ucla'
    elif args in ('wossidia', 'rostock'):
        org = 'wossidia'
    else:
        raise Exception('Invalid organization')

    wd = importlib.orgs[org][4]
    apikey = importlib.apikey

    # if not org Create it
    if not importlib.org_exists(org):
        exit('organization [%s] does not exist.' % org)

    files = [join(wd, f) for f in sorted(listdir(wd)) if f.endswith('.xml') and isfile(join(wd, f))]
    print('get file lists')

    error = list()
    counter = 0
    limit = 50000
    results = set()
    for f in files:
        if counter <= limit:
            counter += 1
            print('### start with file: %s ###' % f)
            # try:
            current_story = get_story_from_xml_file(f)
            current_values = get_unique_field_value_as_set(current_story)
            if current_values:
                results = results.union(current_values)
            # except Exception as ex:
            #     error.append(f)
            #     exit(ex.message)
            print('### end with file: %s ###' % f)
        else:
            break

    if len(error) > 0:
        for i in error:
            print(i)
    print('Number of unique keywords: {}'.format(len(results)))
    end = time.time()
    elapsed = end - start
    print('#### Overview ###')
    print('#### Start at: %s' % start)
    print('#### Ends at: %s' % end)
    print('#### Time elapsed: %s' % elapsed)


if __name__ == '__main__':
    __main__()
