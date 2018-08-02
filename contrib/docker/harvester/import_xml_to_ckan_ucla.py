import urllib2
import urllib
import json
import requests
import xml.etree.ElementTree as et
import hashlib
from os import listdir
from os.path import isfile, join


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

    def parse_xml(self, path):
        # get xml file
        tree = et.parse(path)

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

        return self.data


def create_package(org, f, apikey):
    isebel_list = ['text', 'url', 'datePublished', 'narrator', 'placeOfNarration', 'placeMentioned']
    data = XML().parse_xml(f)
    data['md5'] = md5(f)

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
    apikey = "d75f0539-89f4-41d2-8c0d-92fbd820c53f"
    wd = '/var/harvester/oai-isebel/isebel_ucla'
    org = 'isebel_ucla'
    debug = True
    qty = 10

    # Get current dataset names
    print 'before getting created package'
    created_package = get_created_package(org, apikey)
    print 'after getting created package'
    # Remove all the datasets
    remove_all_created_package(created_package, apikey)

    created_package = get_created_package(org, apikey)
    while len(created_package) > 0:
        created_package = get_created_package(org, apikey)
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
