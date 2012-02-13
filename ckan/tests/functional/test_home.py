from pylons import c, session
from pylons.i18n import set_lang

from ckan.lib.create_test_data import CreateTestData
from ckan.controllers.home import HomeController
import ckan.model as model

from ckan.tests import *
from ckan.tests.html_check import HtmlCheckMethods
from ckan.tests.pylons_controller import PylonsTestCase
from ckan.tests import search_related, setup_test_search_index

class TestHomeController(TestController, PylonsTestCase, HtmlCheckMethods):
    @classmethod
    def setup_class(cls):
        setup_test_search_index()
        PylonsTestCase.setup_class()
        model.repo.init_db()
        CreateTestData.create()
        
    @classmethod
    def teardown_class(self):
        model.repo.rebuild_db()

    def clear_language_setting(self):
        self.app.cookies = {}

    def test_home_page(self):
        offset = url_for('home')
        res = self.app.get(offset)
        assert 'Add a dataset' in res
        assert 'Could not change language' not in res
        assert "Dave's books has 2 datasets" in res, res
        assert "Roger's books has 1 datasets" in res, res

    @search_related
    def test_packages_link(self):
        offset = url_for('home')
        res = self.app.get(offset)
        res.click('Search', index=0)
        
    def test_template_head_end(self):
        offset = url_for('home')
        res = self.app.get(offset)
        assert 'ckan.template_head_end = <link rel="stylesheet" href="TEST_TEMPLATE_HEAD_END.css" type="text/css"> '

    def test_template_head_end(self):
        offset = url_for('home')
        res = self.app.get(offset)
        assert 'ckan.template_head_end = <link rel="stylesheet" href="TEST_TEMPLATE_HEAD_END.css" type="text/css"> '

    def test_template_footer_end(self):
        offset = url_for('home')
        res = self.app.get(offset)
        assert '<strong>TEST TEMPLATE_FOOTER_END TEST</strong>'

## Browser lang detection disabled - see #1452
##    def test_locale_detect(self):
##        offset = url_for('home')
##        self.clear_language_setting()
##        res = self.app.get(offset, headers={'Accept-Language': 'de,pt-br,en'})
##        try:
##            assert 'Willkommen' in res.body, res.body
##        finally:
##            self.clear_language_setting()

##    def test_locale_negotiate(self):
##        offset = url_for('home')
##        self.clear_language_setting()
##        res = self.app.get(offset, headers={'Accept-Language': 'fr-ca'})
##        # Request for French with Canadian territory should negotiate to
##        # just 'fr'
##        try:
##            assert 'propos' in res.body, res.body
##        finally:
##            self.clear_language_setting()

##    def test_locale_negotiate_pt(self):
##        offset = url_for('home')
##        self.clear_language_setting()
##        res = self.app.get(offset, headers={'Accept-Language': 'pt'})
##        # Request for Portuguese should find pt_BR because of our alias hack
##        try:
##            assert 'Bem-vindo' in res.body, res.body
##        finally:
##            self.clear_language_setting()

    def test_locale_change(self):
        offset = url_for('home')
        res = self.app.get(offset)
        res = res.click('Deutsch')
        try:
            res = res.follow()
            assert 'Willkommen' in res.body
        finally:
            self.clear_language_setting()


    def test_update_profile_notice(self):
        edit_url = url_for(controller='user', action='edit')
        email_notice = 'Please <a href="%s">update your profile</a>' \
                ' and add your email address.' % (edit_url)
        fullname_notice = 'Please <a href="%s">update your profile' \
                '</a> and add your full name' % (edit_url)
        email_and_fullname_notice ='Please <a href="%s">update your' \
            ' profile</a> and add your email address and your full name.' \
            % (edit_url)
        url = url_for('home')

        # No update profile notices should be flashed if no one is logged in.
        response = self.app.get(url)
        assert email_notice not in response
        assert fullname_notice not in response
        assert email_and_fullname_notice not in response

        # Make some test users.
        user1 = model.user.User(name='user1', fullname="user 1's full name",
                email='user1@testusers.org')
        user2 = model.user.User(name='user2', fullname="user 2's full name")
        user3 = model.user.User(name='user3', email='user3@testusers.org')
        user4 = model.user.User(name='user4')

        # Some test users with Google OpenIDs.
        user5 = model.user.User(
                    name='https://www.google.com/accounts/o8/id/id=ACyQatixLeL'
                         'ODscWvwqsCXWQ2sa3RRaBhaKTkcsvUElI6tNHIQ1_egX_wt1x3fA'
                         'Y983DpW4UQV_U',
                    fullname="user 5's full name", email="user5@testusers.org")
        user6 = model.user.User(
                    name='https://www.google.com/accounts/o8/id/id=ACyQatixLeL'
                         'ODscWvwqsCXWQ2sa3RRaBhaKTkcsvUElI6tNHIQ1_egX_wt1x3fA'
                         'Y983DpW4UQV_J',
                    fullname="user 6's full name")
        user7 = model.user.User(
                    name='https://www.google.com/accounts/o8/id/id=AItOawl27F2'
                         'M92ry4jTdjiVx06tuFNA',
                    email='user7@testusers.org')
        user8 = model.user.User(
                    name='https://www.google.com/accounts/o8/id/id=AItOawl27F2'
                         'M92ry4jTdjiVx06tuFNs'
                    )

        users = (user1, user2, user3, user4, user5, user6, user7, user8)
        google_users = (user5, user6, user7, user8)

        for user in users:
            model.repo.new_revision()
            model.Session.add(user)
            model.Session.commit()

            response = self.app.get(url, extra_environ={'REMOTE_USER':
                user.name.encode('utf-8')})

            model.repo.new_revision()
            model.Session.add(user)

            if user in google_users:
                # Users with Google OpenIDs are asked to give their email if
                # they don't have one and to enter a full name if they don't
                # have one.
                if not user.email and not user.fullname:
                    assert email_and_fullname_notice in response
                    assert email_notice not in response
                    assert fullname_notice not in response
                elif user.email and not user.fullname:
                    assert email_notice not in response
                    assert fullname_notice in response
                    assert email_and_fullname_notice not in response
                elif not user.email and user.fullname:
                    assert email_notice in response
                    assert fullname_notice not in response
                    assert email_and_fullname_notice not in response
                elif user.email and user.fullname:
                    assert email_notice not in response
                    assert fullname_notice not in response
                    assert email_and_fullname_notice not in response
            else:
                # Users without Google OpenIDs are just asked to give their
                # email if they don't have one.
                if not user.email:
                    assert email_notice in response
                    assert email_and_fullname_notice not in response
                    assert fullname_notice not in response
                elif user.email:
                    assert email_notice not in response
                    assert fullname_notice not in response
                    assert email_and_fullname_notice not in response

            if not user.email:
                user.email = "mr_tusks@tusk_family.org"
            if not user.fullname:
                user.fullname = "Mr. Tusks"
            model.Session.commit()

            response = self.app.get(url, extra_environ={'REMOTE_USER':
                user.name.encode('utf-8')})
            assert email_notice not in response
            assert fullname_notice not in response
            assert email_and_fullname_notice not in response

class TestHomeControllerWithoutSearch(TestController, PylonsTestCase, HtmlCheckMethods):
    @classmethod
    def setup_class(cls):
        PylonsTestCase.setup_class()
        
    @classmethod
    def teardown_class(self):
        model.repo.rebuild_db()
        
    def test_404(self):
        offset = '/some_nonexistent_url'
        res = self.app.get(offset, status=404)

    def test_about(self):
        offset = url_for(controller='home', action='about')
        res = self.app.get(url_for('about'))
        assert 'CKAN is a community-run catalogue' in res.body, res.body


class TestDatabaseNotInitialised(TestController):
    @classmethod
    def setup_class(cls):
        PylonsTestCase.setup_class()
        model.repo.clean_db()

    @classmethod
    def teardown_class(self):
        model.repo.rebuild_db()

    def test_home_page(self):
        offset = url_for('home')
        res = self.app.get(offset, status=503)
        assert 'This site is currently off-line. Database is not initialised.' in res
