# -*- coding: utf-8 -*-
import os
import time
import sys

import import_xml_to_ckan_util as importlib


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

    original_target_folder = '{}_{}'.format(importlib.orgs[org][3], importlib.machine_translation_target)
    wd = os.path.join(importlib.machine_translation_target_path, original_target_folder)

    print('get file lists')
    for f in os.listdir(wd):
        print('### start with file: %s ###' % f)

        filename_parts_list = f.split('.')
        story_global_identifier = '.'.join([i for i in filename_parts_list[1:4]])

        old_translation = importlib.get_extra_data_field(importlib.apikey, story_global_identifier,
                                                         'machine_translation_target')
        print('old translation: {}'.format(old_translation))
        new_translation = importlib.get_new_translation_from_file(org, story_global_identifier)
        if new_translation:
            print('new translation: {}'.format(new_translation.encode('utf-8')))
        else:
            print('no new translation. skipping...')
            continue

        if old_translation != new_translation:
            print('should update')
            if old_translation:
                importlib.set_extra_data_field(importlib.apikey, story_global_identifier, 'machine_translation_target',
                                               "{}\n{}".format(new_translation.encode("utf-8"),
                                                               old_translation.encode("utf-8")))
            else:
                importlib.set_extra_data_field(importlib.apikey, story_global_identifier, 'machine_translation_target',
                                               new_translation.encode("utf-8"))
        else:
            print('do NOT update')

        print('### end with file: %s ###' % f)
    end = time.time()
    elapsed = end - start
    print('#### Overview ###')
    print('#### Start at: %s' % start)
    print('#### Ends at: %s' % end)
    print('#### Time elapsed: %s' % elapsed)


__main__()
