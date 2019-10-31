# -*- coding: utf-8 -*-
import argparse
import fnmatch
import os
import sys
from lxml import etree
from termcolor import colored


def recursive_glob(treeroot, wd, pattern):
    for base, dirs, files in os.walk(treeroot):
        file_list = fnmatch.filter(files, pattern)
        for f in file_list:
            yield(os.path.join(wd, base, f))


def help_message():
    stderr("use: python testxmlvalidate.py -d directory")
    sys.exit(0)


def stderr(text):
    sys.stderr.write("{}\n".format(text))


def stdout(text):
    sys.stdout.write("{}\n".format(text))


def arguments():
    ap = argparse.ArgumentParser(description='Read and check files from "Isebel"')
    ap.add_argument('-d', '--directory', help="directory")
    ap.add_argument('-s', '--schema', help="schema", default='/var/harvester/isebel-schema/xsd_test/isebel2.xsd')
    ap.add_argument('-r', '--root', help="root", default='/var/harvester')
    ap.add_argument('-p', '--pattern', help="file pattern", default='*.xml')
    args = vars(ap.parse_args())
    return args


def validate(xml_file):
    global xml_schema

    with open(xml_file, 'r') as fh:
        xml_doc = etree.parse(fh)
        xml_schema.assertValid(xml_doc)


if __name__ == "__main__":

    args = arguments()
    wd = args.get('wd', '/var/harvester')
    pattern = args.get('pattern', "*.xml")
    directory = args.get('directory', None)
    xsd_file = args.get('schema')

    error_list = list()

    if not directory:
        help_message()

    if not os.path.exists(xsd_file):
        exit('Missing schema: {}'.format(xsd_file))
    else:
        # preparing XSD schema
        try:
            schema_doc = etree.parse(xsd_file)
            xml_schema = etree.XMLSchema(schema_doc)
        except Exception as ex:
            exit('Invalid schema: {}, error: {}'.format(xsd_file, ex))

    print("Validating .........................\n")
    for filename in recursive_glob(directory, wd, pattern):
        print(colored('validating {}'.format(filename), 'blue'))
        try:
            validate(filename)
            # print(colored('{} is valid'.format(filename), 'green'))
        except Exception as ex:
            print(colored('{} is not valid, error detail: {}'.format(filename, repr(ex)), 'red'))
            error_list.append('{} is not valid\n error detail: {}\n'.format(filename, repr(ex)))
    print(colored("............................. Validation Finished ..............................", 'blue'))
    print(colored("............................. Validation Result Overview ..............................", 'blue'))
    if len(error_list) == 0:
        print(colored("Everything is valid", 'green'))
    else:
        print(colored("Please check for the errors below", 'red'))
        for i in error_list:
            print(colored("{}".format(i), 'red'))
