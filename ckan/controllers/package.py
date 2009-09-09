import logging
import genshi
import simplejson

from ckan.lib.base import *
from ckan.controllers.base import CkanBaseController
from ckan.lib.search import Search, SearchOptions
import ckan.forms

logger = logging.getLogger('ckan.controllers')

class ValidationException(Exception):
    pass

class PackageController(CkanBaseController):

    def index(self):
        c.package_count = model.Package.query.count()
        return render('package/index')

    def list(self, id=0, format='html'):
        c.format = format
        return self._paginate_list('package', id, 'package/list',
            ['name', 'title'])

    def search(self):
        request_params = dict(request.params)
        c.show_results = False
        if request_params.has_key('q'):
            c.q = request_params['q']
            c.open_only = request_params.has_key('open_only')
            c.downloadable_only = request_params.has_key('downloadable_only')
            options = SearchOptions({'q':c.q,
                                     'filter_by_openness':c.open_only,
                                     'filter_by_downloadable':c.downloadable_only,
                                     'return_objects':True,
                                     })
            results = Search().run(options)
            c.packages = results['results']
            c.package_count = results['count']

            options.entity = 'tag'
            results = Search().run(options)
            c.tags = results['results']
            c.tags_count = results['count']

            c.show_results = True
        return render('package/search')

    def read(self, id):
        c.pkg = model.Package.by_name(id)
        if c.pkg is None:
            abort(404, '404 Not Found')
        fs = ckan.forms.package_fs.bind(c.pkg)
        c.content = genshi.HTML(self._render_package(fs))
        return render('package/read')

    def history(self, id):
        c.pkg = model.Package.by_name(id)
        if not c.pkg:
            abort(404, '404 Not Found')
        c.revisions = c.pkg.all_revisions
        return render('package/history')

    def new(self):
        c.has_autocomplete = True
        c.error = ''

        if request.params.has_key('commit'):
            record = model.Package
            fs = ckan.forms.package_fs.bind(record, data=request.params or None)
            try:
                self._update(fs, id, record.id)
                c.pkgname = fs.name.value
                h.redirect_to(action='read', id=c.pkgname)
            except ValidationException, error:
                c.error, fs = error.args
                c.form = self._render_edit_form(fs)
                return render('package/edit')

        # use request params even when starting to allow posting from "outside"
        # (e.g. bookmarklet)
        if request.params:
            data = ckan.forms.edit_package_dict(ckan.forms.get_package_dict(), request.params)
            fs = ckan.forms.package_fs.bind(data=data)
        else:
            fs = ckan.forms.package_fs
        c.form = self._render_edit_form(fs)
        if 'preview' in request.params:
            c.preview = genshi.HTML(self._render_package(fs))
        return render('package/new')

    def edit(self, id=None): # allow id=None to allow posting
        # TODO: refactor to avoid duplication between here and new
        c.has_autocomplete = True
        c.error = ''
        if not 'commit' in request.params and not 'preview' in request.params:
            # edit
            c.pkg = model.Package.by_name(id)
            if c.pkg is None:
                abort(404, '404 Not Found')
                
            fs = ckan.forms.package_fs.bind(c.pkg)
            c.form = self._render_edit_form(fs)
            return render('package/edit')
        elif request.params.has_key('commit'):
            # id is the name (pre-edited state)
            c.pkgname = id
            record = model.Package.by_name(c.pkgname)
            params = dict(request.params) # needed because request is nested
                                          # multidict which is read only
            c.fs = ckan.forms.package_fs.bind(record, data=params or None)
            try:
                self._update(c.fs, id, record.id)

                # do not use pkgname from id as may have changed
                c.pkgname = c.fs.name.value
                h.redirect_to(action='read', id=c.pkgname)
            except ValidationException, error:
                c.error, fs = error.args
                c.form = self._render_edit_form(fs)
                return render('package/edit')
        else: # Must be preview
            c.pkgname = id
            record = model.Package.by_name(c.pkgname)
            fs = ckan.forms.package_fs.bind(record, data=request.params)
            c.form = self._render_edit_form(fs)
            c.preview = genshi.HTML(self._render_package(fs))
            return render('package/edit')
    
    def _render_edit_form(self, fs):
        # errors arrive in c.error and fs.errors
        c.form = fs.render()
        return render('package/edit_form')
        
    def _is_locked(pkgname, self):
        # allow non-existent name -- never happens but allows test of 'bad'
        # update (test_update in test_package.py) to work normally :)
        if pkgname == 'mis-uiowa':
            msg = 'This package is temporarily locked and cannot be edited'
            raise msg
        return ''

    def _is_spam(self, log_message):
        if log_message and 'http:' in log_message:
            return True
        return False

    def _update(self, fs, id, record_id):
        '''
        Writes the POST data to the database
        @input c.error
        '''
        error_msg = self._is_locked(fs.name.value)
        if error_msg:
            raise Exception(error_msg)

        log_message = request.params['log_message']
        if self._is_spam(log_message):
            error_msg = 'This commit looks like spam'
            # TODO: make this into a UserErrorMessage or the like
            raise Exception(error_msg)

        # currently only returns one value because of problems with
        # genshi and multiple on select so need to wrap in an array
##        if request.params.has_key('licenses'):
##            indict['licenses'] = [request.params['licenses']]
##        else:
##            indict['licenses'] = []

        validation = fs.validate_on_edit(id, record_id)
        if not validation:
            errors = []            
            for field, err_list in fs.errors.items():
                errors.append("%s:%s" % (field.name, ";".join(err_list)))
            c.error = ', '.join(errors)
            c.form = self._render_edit_form(fs)
            raise ValidationException(c.error, fs)

        try:
            rev = model.repo.new_revision()
            rev.author = c.author
            rev.message = log_message

            fs.sync()
        except Exception, inst:
            model.Session.rollback()
            raise
        else:
            model.Session.commit()

    def _render_package(self, fs):
        # Todo: More specific error handling (don't catch-all and set 500)?
#        try:
            c.pkg_name = fs.name.value
            c.pkg_version = fs.version.value
            c.pkg_title = fs.title.value
            c.pkg_url = fs.url.value
            c.pkg_download_url = fs.download_url.value
            c.pkg_author = fs.author.value
            c.pkg_author_email = fs.author_email.value
            c.pkg_maintainer = fs.maintainer.value
            c.pkg_maintainer_email = fs.maintainer_email.value
            if fs.license.value:
                c.pkg_license = model.License.query.get(fs.license.value).name
            else:
                c.pkg_license = None
            if fs.tags.value:
                c.pkg_tags = [tag.name for tag in fs.tags.value]
            elif fs.model.tags:
                c.pkg_tags = [tag.name for tag in fs.model.tags]
            else:
                c.pkg_tags = []
##            if fs.groups.value:
##                c.pkg_groups = [group.name for group in fs.groups.value]
            if fs.model.groups:
                c.pkg_groups = [group.name for group in fs.model.groups]
            else:
                c.pkg_groups = []
            import ckan.misc
            format = ckan.misc.MarkdownFormat()
            notes_formatted = format.to_html(fs.notes.value)
            notes_formatted = genshi.HTML(notes_formatted)
            c.pkg_notes_formatted = notes_formatted
            preview = render('package/read_content')
#        except Exception, inst:
#            self.status_code = 500
#            preview = 'There was an error rendering the package: %s' % inst
            return preview




