import logging
from urllib import urlencode

from ckan.lib.base import BaseController, c, model, request, render, h, g
from ckan.lib.base import ValidationException, abort, gettext
from pylons.i18n import get_lang, _
import ckan.authz as authz
from ckan.lib.alphabet_paginate import AlphaPage
from ckan.lib.navl.dictization_functions import DataError, unflatten, validate
from ckan.authz import Authorizer
from ckan.logic import NotFound, NotAuthorized, ValidationError
from ckan.logic import check_access, get_action
from ckan.logic import tuplize_dict, clean_dict, parse_params
from ckan.lib.dictization.model_dictize import package_dictize
import ckan.forms
import ckan.model as model
from ckan.lib.navl.validators import (ignore_missing,
                                      not_empty,
                                      empty,
                                      ignore,
                                      keep_extras,)

class OrganizationController(BaseController):

    def _send_application( self, group, reason  ):
        from ckan.logic.action import error_summary
        from ckan.lib.mailer import mail_recipient
        from genshi.template.text import NewTextTemplate
        from pylons import config

        if not reason:
            h.flash_error(_("There was a problem with your submission, \
                             please correct it and try again"))
            errors = {"reason": ["No reason was supplied"]}
            return self.apply(group.id, errors=errors,
                              error_summary=error_summary(errors))

        admins = group.members_of_type( model.User, 'admin' ).all()
        recipients = [(u.fullname,u.email) for u in admins] if admins else \
                     [(config.get('dgu.admin.name', "DGU Admin"),
                       config.get('dgu.admin.email', None), )]

        if not recipients:
            h.flash_error(_("There is a problem with the system configuration"))
            errors = {"reason": ["No group administrator exists"]}
            return self.apply(group.id, data=data, errors=errors,
                              error_summary=error_summary(errors))

        extra_vars = {
            'group'    : group,
            'requester': c.userobj,
            'reason'   : reason
        }
        email_msg = render("email/join_publisher_request.txt", extra_vars=extra_vars,
                         loader_class=NewTextTemplate)

        try:
            for (name,recipient) in recipients:
                mail_recipient(name,
                               recipient,
                               "Publisher request",
                               email_msg)
        except:
            h.flash_error(_("There is a problem with the system configuration"))
            errors = {"reason": ["No mail server was found"]}
            return self.apply(group.id, errors=errors,
                              error_summary=error_summary(errors))

        h.flash_success(_("Your application has been submitted"))
        h.redirect_to( 'publisher_read', id=group.name)

    def apply(self, id=None, data=None, errors=None, error_summary=None):
        """
        A user has requested access to this publisher and so we will send an
        email to any admins within the publisher.
        """
        if 'parent' in request.params and not id:
            id = request.params['parent']

        if id:
            c.group = model.Group.get(id)
            if 'save' in request.params and not errors:
                return self._send_application(c.group, request.params.get('reason', None))

        self._add_publisher_list()
        data = data or {}
        errors = errors or {}
        error_summary = error_summary or {}

        data.update(request.params)

        vars = {'data': data, 'errors': errors, 'error_summary': error_summary}
        c.form = render('organization_apply_form.html', extra_vars=vars)
        return render('organization_apply.html')

    def _add_users( self, group, parameters  ):
        from ckan.logic.schema import default_group_schema
        from ckan.logic.action import error_summary
        from ckan.lib.dictization.model_save import group_member_save

        if not group:
            h.flash_error(_("There was a problem with your submission, \
                             please correct it and try again"))
            errors = {"reason": ["No reason was supplied"]}
            return self.apply(group.id, errors=errors,
                              error_summary=error_summary(errors))

        data_dict = clean_dict(unflatten(
                tuplize_dict(parse_params(request.params))))
        data_dict['id'] = group.id

        # Temporary fix for strange caching during dev
        l = data_dict['users']
        for d in l:
            d['capacity'] = d.get('capacity','editor')

        context = {
            "group" : group,
            "schema": default_group_schema(),
            "model": model,
            "session": model.Session
        }

        # Temporary cleanup of a capacity being sent without a name
        users = [d for d in data_dict['users'] if len(d) == 2]
        data_dict['users'] = users

        model.repo.new_revision()
        group_member_save(context, data_dict, 'users')
        model.Session.commit()

        h.redirect_to( controller='group', action='edit', id=group.name)


    def users(self, id, data=None, errors=None, error_summary=None):
        c.group = model.Group.get(id)

        if not c.group:
            abort(404, _('Group not found'))

        context = {
                   'model': model,
                   'session': model.Session,
                   'user': c.user or c.author,
                   'group': c.group }

        try:
            check_access('group_update',context)
        except NotAuthorized, e:
            abort(401, _('User %r not authorized to edit %s') % (c.user, id))

        if 'save' in request.params and not errors:
            return self._add_users(c.group, request.params)

        data = data or {}
        errors = errors or {}
        error_summary = error_summary or {}

        data['users'] = []
        data['users'].extend( { "name": user.name,
                                "capacity": "admin" }
                                for user in c.group.members_of_type( model.User, "admin"  ).all() )
        data['users'].extend( { "name": user.name,
                                "capacity": "editor" }
                                for user in c.group.members_of_type( model.User, 'editor' ).all() )

        vars = {'data': data, 'errors': errors, 'error_summary': error_summary}
        c.form = render('organization_users_form.html', extra_vars=vars)

        return render('organization_users.html')

    def _add_publisher_list(self):
        c.possible_parents = model.Session.query(model.Group).\
               filter(model.Group.state == 'active').\
               filter(model.Group.type == 'organization').\
               order_by(model.Group.title).all()

