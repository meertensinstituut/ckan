from ckan.lib.base import *
from ckan.controllers.base import CkanBaseController
import pylons.controllers.util as util

def login_form():
    return render('account/login_form').replace('FORM_ACTION', '%s')

class AccountController(CkanBaseController):

    def index(self):
        if not c.user:
            util.redirect_to(controller='account', action='login', id=None)
        else:
            q = model.Revision.query.filter_by(author=c.user).limit(20)
            c.activity = q.limit(20).all()            
            return render('account/index')

#     def login_form(self, return_url=''):
#         return render('account/login_form')
# 
#     def openid_form(self, return_url=''):
#         return render('account/openid_form').replace('DOLAR', '$')
# 
    def login(self):
        if c.user:
            h.redirect_to(controller='account', action=None, id=None)
        else:
            form = render('account/openid_form')
            # /login_openid page need not exist -- request gets intercepted by openid plugin
            form = form.replace('FORM_ACTION', '/login_openid')
            return form

    def logout(self):
        c.user = None
        return render('account/logout')

    def apikey(self):
        # logged in
        if not c.user:
            abort(401)
        else:
            username = c.author
            apikey_object = model.ApiKey.by_name(username)
            if apikey_object is None:
                apikey_object = model.ApiKey(name=username)
                model.Session.commit()
            c.api_key = apikey_object.key
        return render('account/apikey')

