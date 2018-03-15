'''
This script fixes resource extras affected by a bug introduced in #3425 and
raised in #4042

#3422 (implemented in #3425) introduced a major bug where if a resource was
deleted and the DataStore was active, extras from all resources on the site
where changed. This is now fixed starting from version 2.7.3 but if your
database is already affected you will need to run this script to restore
the extras to their previous state.

Remember, you only need to run this script if all the following are true:

     1. You are currently running CKAN 2.7.0 or 2.7.2, and
     2. You have enabled the DataStore, and
     3. One or more resources with data on the DataStore have been deleted
        (or your suspect they might have been)

If all these are true you can run this script like this:

    python fix_resource_extras.py -c path/to/the/ini/file

As ever when making changes in the database please do a backup before running
this script.

Note that it requires SQLAlchemy, so you should run it with the virtualenv
activated.
'''

from ConfigParser import ConfigParser
from argparse import ArgumentParser
from sqlalchemy import create_engine
from sqlalchemy.sql import text

config = ConfigParser()
parser = ArgumentParser()
parser.add_argument('-c', '--config', help='Configuration file', required=True)

SIMPLE_Q = (
    "SELECT id, r.extras, rr.extras revision "
    "FROM resource r JOIN resource_revision rr "
    "USING(id, revision_id) WHERE r.extras != rr.extras"
)
UPDATE_Q = text("UPDATE resource SET extras = :extras WHERE id = :id")


def main():
    args = parser.parse_args()
    config.read(args.config)
    engine = create_engine(config.get('app:main', 'sqlalchemy.url'))
    records = engine.execute(SIMPLE_Q)

    total = records.rowcount
    print('Found {} datasets with inconsistent extras.'.format(total))
    print()

    skip_confirmation = False
    i = 0

    while True:
        row = records.fetchone()
        if row is None:
            break

        id, current, rev = row
        if dict(current, datastore_active=None) == dict(rev, datastore_active=None):
            continue
        i += 1

        print('[{:{}}/{}] Resource <{}>'.format(i, len(str(total)), total, id))
        print('\tCurrent extras state in DB: {}'.format(current))
        print('\tAccording to the revision:  {}'.format(rev))
        if not skip_confirmation:
            choice = raw_input(
                '\tRequired action: '
                'y - rewrite; n - skip; ! - rewrite all; q - skip all: '
            ).strip()
            if choice == 'q':
                break
            elif choice == 'n':
                continue
            elif choice == '!':
                skip_confirmation = True
        engine.execute(UPDATE_Q, id=id, extras=rev)
        print('\tUpdated')


if __name__ == '__main__':
    main()
