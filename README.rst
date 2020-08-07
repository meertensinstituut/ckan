ISEBEL
======

ISEBEL runs on CKAN
-------------------

.. image:: https://img.shields.io/badge/license-AGPL-blue.svg?style=flat
    :target: https://opensource.org/licenses/AGPL-3.0
    :alt: License

.. image:: https://img.shields.io/badge/docs-latest-brightgreen.svg?style=flat
    :target: http://docs.ckan.org
    :alt: Documentation
.. image:: https://img.shields.io/badge/support-StackOverflow-yellowgreen.svg?style=flat
    :target: https://stackoverflow.com/questions/tagged/ckan
    :alt: Support on StackOverflow

.. image:: https://circleci.com/gh/ckan/ckan.svg?style=shield
    :target: https://circleci.com/gh/ckan/ckan
    :alt: Build Status

.. image:: https://coveralls.io/repos/github/ckan/ckan/badge.svg?branch=master
    :target: https://coveralls.io/github/ckan/ckan?branch=master
    :alt: Coverage Status

**CKAN is the world’s leading open-source data portal platform**.
CKAN makes it easy to publish, share and work with data. It's a data management
system that provides a powerful platform for cataloging, storing and accessing
datasets with a rich front-end, full API (for both data and catalog), visualization
tools and more. Read more at `ckan.org <http://ckan.org/>`_.


Original CKAN Installation
--------------------------

See the `CKAN Documentation <http://docs.ckan.org>`_ for installation instructions.

Easy start using docker
-----------------------
  * Create folder for isebel: `mkdir isebel && cd isebel`
  * Create folder for source code in folder isebel: `mkdir code_dev`
  * Clone ckan repository with the submodule: `git clone --recurse-submodules -j8 ckan`
  * Create a production.ini file in folder ckan/contrib/docker/ (under newly cloned CKAN)
  * Go to code_dev folder: `cd code_dev`
  * Clone ISEBEL CKAN extension: `git clone https://github.com/vicding-mi/ckanext-facet.git`
  * Clone B2Find CKAN extension: `git clone https://github.com/vicding-mi/ckanext-timeline.git`
  * Clone OAI-PMH harvester: `git clone https://github.com/meertensinstituut/oai-pmh/tree/development harvester_src`
  * Clone translator scripts: `git clone https://git.informatik.uni-rostock.de/isebel/translation-thesaurus.git` (optional)
  * Go to ckan folder: `cd ../ckan`
  * Go to docker subfolder: `cd contrib/docker`
  * Start the whole setup: `./start-ckan.sh`
  * Add admin user: `docker exec -it ckan /usr/local/bin/ckan-paster --plugin=ckan sysadmin -c /etc/ckan/production.ini add ckan_admin`
  * Stop the whole setup: `./stop-ckan.sh`

  ** NOTE: the stop script will prune all the stopped containers (including the containers from other projects)


ISEBEL infrastructure diagram
-----------------------------

ISEBEL consists of multiple components. CKAN is her data management system. Solr is the indexer, Postgre is the database server
and OAI PMH harvester manager as the harvester for the data provider. There are underlining components which is listed below:

  1. Translater which machine translates the stories (N-to-N)
  2. Extracter which extracts the keywords (so called machine generated keywords)
  3. Merger which merges the machine generated keywords with the manual keywords
  4. The importer which imports harvested data into CKAN
  5. The merger which links manual

![Image of Yaktocat](https://octodex.github.com/images/yaktocat.png)

Support
-------

  * If you have ISEBEL related question and issue, please open an issue.
  * If you need help with CKAN or want to ask a question, use either the `ckan-dev`_ mailing list or the `CKAN tag on Stack Overflow`_ (try searching the Stack Overflow and ckan-dev `archives`_ for an answer to your question first).
  * If you've found a bug in CKAN, open a new issue on CKAN's `GitHub Issues`_ (try searching first to see if there's already an issue for your bug).
  * If you find a potential security vulnerability please email security@ckan.org, rather than creating a public issue on GitHub.


Contributing to CKAN
--------------------

For contributing to CKAN or its documentation, see
`CONTRIBUTING <https://github.com/ckan/ckan/blob/master/CONTRIBUTING.rst>`_.

If you want to talk about CKAN development say hi to the CKAN developers on the
`ckan-dev`_ mailing list, in the `#ckan`_ IRC channel, or on `BotBot`_.

If you've figured out how to do something with CKAN and want to document it for
others, make a new page on the `CKAN wiki`_, and tell us about it on
ckan-dev mailing list.

.. _Link to the Diagram: https://google.com/
.. _ckan-dev: http://lists.okfn.org/mailman/listinfo/ckan-dev
.. _#ckan: http://webchat.freenode.net/?channels=ckan
.. _CKAN Wiki: https://github.com/ckan/ckan/wiki
.. _BotBot: https://botbot.me/freenode/ckan/
.. _Google Group: https://groups.google.com/forum/#!forum/ckan-global-user-group
.. _CKAN tag on Stack Overflow: http://stackoverflow.com/questions/tagged/ckan
.. _archives: https://www.google.com/search?q=%22%5Bckan-dev%5D%22+site%3Alists.okfn.org.
.. _GitHub Issues: https://github.com/ckan/ckan/issues

Copying and License
-------------------

This material is copyright (c) 2006-2018 Open Knowledge International and contributors.

It is open and licensed under the GNU Affero General Public License (AGPL) v3.0
whose full text may be found at:

http://www.fsf.org/licensing/licenses/agpl-3.0.html
