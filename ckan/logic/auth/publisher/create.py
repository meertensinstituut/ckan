from ckan.logic.auth import get_package_object, get_group_object, get_authorization_group_object, \
    get_user_object, get_resource_object
from ckan.logic.auth.publisher import _groups_intersect    
from ckan.logic import NotFound
from ckan.authz import Authorizer
from ckan.lib.base import _


def package_create(context, data_dict=None):
    model = context['model']
    user = context['user']
    userobj = model.User.get( user )
    
    if userobj:
        return {'success': True}
        
    return {'success': False, 'msg': 'You must be logged in to create a package'}
    

def resource_create(context, data_dict):
    return {'success': False, 'msg': 'Not implemented yet in the auth refactor'}

def package_relationship_create(context, data_dict):
    """
    Permission for users to create a new package relationship requires that the 
    user share a group with both packages.
    """
    model = context['model']
    user = context['user']

    id = data_dict.get('id', '')
    id2 = data_dict.get('id2', '')
    
    pkg1 = model.Package.get(id)
    pkg2 = model.Package.get(id2)
    
    if not pkg1 or not pkg2:
        return {'success': False, 'msg': _('Two package IDs are required')}    
        
    pkg1grps = pkg1.get_groups('publisher')
    pkg2grps = pkg2.get_groups('publisher')

    usergrps = model.User.get( user ).get_groups('publisher')
    authorized = _groups_intersect( usergrps, pkg1grps ) and _groups_intersect( usergrps, pkg2grps )    
    if not authorized:
        return {'success': False, 'msg': _('User %s not authorized to edit these packages') % str(user)}
    else:
        return {'success': True}

def group_create(context, data_dict=None):
    """
    Group create permission.  If a group is provided, within which we want to create a group
    then we check that the user is within that group.  If not then we just say Yes for now 
    although there may be some approval issues elsewhere.
    """
    model = context['model']
    user  = context['user']

    if not user:
        return {'success': False, 'msg': _('User is not authorized to create groups') }        
   
    try:
        # If the user is doing this within another group then we need to make sure that
        # the user has permissions for this group.
        group = get_group_object( context )
    except NotFound:
        return { 'success' : True }
        
    userobj = model.User.get( user )
    if not userobj:
        return {'success': False, 'msg': _('User %s not authorized to create groups') % str(user)}        
        
    authorized = _groups_intersect( userobj.get_groups('publisher'), [group] )
    if not authorized:
        return {'success': False, 'msg': _('User %s not authorized to create groups') % str(user)}
    else:
        return {'success': True}

def authorization_group_create(context, data_dict=None):
    return {'success': False, 'msg': _('Authorization groups not implemented in this profile') % str(user)}


def rating_create(context, data_dict):
    # No authz check in the logic function
    return {'success': True}

def user_create(context, data_dict=None):
    return {'success': True}


def check_group_auth(context, data_dict):
    # Maintained for function count in profiles, until we can rename to _*
    return True

## Modifications for rest api

def package_create_rest(context, data_dict):
    model = context['model']
    user = context['user']
    if user in (model.PSEUDO_USER__VISITOR, ''):
        return {'success': False, 'msg': _('Valid API key needed to create a package')}

    return package_create(context, data_dict)

def group_create_rest(context, data_dict):
    model = context['model']
    user = context['user']
    if user in (model.PSEUDO_USER__VISITOR, ''):
        return {'success': False, 'msg': _('Valid API key needed to create a group')}

    return group_create(context, data_dict)
