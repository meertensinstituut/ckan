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
        full_path = os.path.join(wd, f)
        if not os.path.isfile(full_path):
            print('Not file, skipping...')
            continue

        filename_parts_list = f.split('.')
        # get global id from filename; not reliable but still the best way to go for now
        if org == 'meertens' or org == 'ucla':
            story_global_identifier = '.'.join([i for i in filename_parts_list[1:4]])
            story_global_identifier = story_global_identifier.replace('.', '-')
        elif org == 'wossidia':
            # story_global_identifier = 'de-wossidia-' + filename_parts_list[1].replace('_', "-")
            story_global_identifier = '-'.join(filename_parts_list[1:4])
        else:
            raise Exception('Invalid organization')

        # get old translation from record
        old_translation = importlib.get_extra_data_field(importlib.apikey, story_global_identifier, 'machine_translation_target')
        if old_translation and type(old_translation) is not unicode:
            old_translation = u"{}".format(old_translation.decode("utf-8"))

        if not old_translation:
            # set old translation to empty string if there is no translation in current story
            old_translation = u""
        if old_translation == u"no record":
            # skip the story if there is no such record
            print("no such story {}. skipping!".format(story_global_identifier))
            continue

        print('old translation: {}'.format(old_translation.encode("utf-8")))
        new_translation = u"{}".format(importlib.get_new_translation_from_file(full_path))
        if new_translation:
            print('new translation: {}'.format(new_translation.encode('utf-8')))
        else:
            print('no new translation. skipping...')
            continue

        try:
            if old_translation != new_translation:
                print('should update')
                if old_translation:
                    if importlib.set_extra_data_field(importlib.apikey, story_global_identifier,
                                                      'machine_translation_target',
                                                      "{}\n{}".format(new_translation.encode("utf-8"),
                                                                      old_translation.encode("utf-8"))):
                        print("update succeed")
                    else:
                        print("update skipped or failed")
                else:
                    if importlib.set_extra_data_field(importlib.apikey, story_global_identifier,
                                                      'machine_translation_target',
                                                      new_translation.encode("utf-8")):
                        print("update succeed")
                    else:
                        print("update skipped or failed")
            else:
                print('do NOT update')
        # except UnicodeDecodeError as ex:
        #     print("UnicodeDecodeError; old_translation: {}; new_translation: {}".format(type(old_translation), type(new_translation)))
        #     exit(ex)
        except AttributeError as ex:
            print("AttributeError; old_translation: {}; new_translation: {}".format(type(old_translation),
                                                                                    type(new_translation)))
            exit(ex)
        print('### end with file: %s ###' % f)
    end = time.time()
    elapsed = end - start
    print('#### Overview ###')
    print('#### Start at: %s' % start)
    print('#### Ends at: %s' % end)
    print('#### Time elapsed: %s' % elapsed)


__main__()
