from sqlalchemy.sql import select
from sqlalchemy import or_

from ckan.logic import NotFound, check_access
from ckan.plugins import (PluginImplementations,
                          IGroupController,
                          IPackageController)
import ckan.authz

from ckan.lib.dictization import table_dictize
from ckan.lib.dictization.model_dictize import (package_dictize,
                                                resource_list_dictize,
                                                group_dictize,
                                                tag_dictize)

from ckan.lib.dictization.model_dictize import (package_to_api1,
                                                package_to_api2,
                                                group_to_api1,
                                                group_to_api2,
                                                tag_to_api1,
                                                tag_to_api2)
from ckan.lib.search import query_for

def package_list(context, data_dict):
    '''Lists the package by name'''
    model = context["model"]
    user = context["user"]
    api = context.get("api_version", '1')
    ref_package_by = 'id' if api == '2' else 'name'

    query = ckan.authz.Authorizer().authorized_query(user, model.Package)
    packages = query.all()
    return [getattr(p, ref_package_by) for p in packages]

def current_package_list_with_resources(context, data_dict):
    model = context["model"]
    user = context["user"]
    limit = data_dict.get("limit")

    q = ckan.authz.Authorizer().authorized_query(user, model.PackageRevision)
    q = q.filter(model.PackageRevision.state=='active')
    q = q.filter(model.PackageRevision.current==True)

    q = q.order_by(model.package_revision_table.c.revision_timestamp.desc())
    if limit:
        q = q.limit(limit)
    pack_rev = q.all()
    package_list = []
    for package in pack_rev:
        result_dict = table_dictize(package, context)
        res_rev = model.resource_revision_table
        resource_group = model.resource_group_table
        q = select([res_rev], from_obj = res_rev.join(resource_group, 
                   resource_group.c.id == res_rev.c.resource_group_id))
        q = q.where(resource_group.c.package_id == package.id)
        result = q.where(res_rev.c.current == True).execute()
        result_dict["resources"] = resource_list_dictize(result, context)
        license_id = result_dict['license_id']
        if license_id:
            isopen = model.Package.get_license_register()[license_id].isopen()
            result_dict['isopen'] = isopen
        else:
            result_dict['isopen'] = False
        package_list.append(result_dict)
    return package_list

def revision_list(context, data_dict):

    model = context["model"]
    revs = model.Session.query(model.Revision).all()
    return [rev.id for rev in revs]

def package_revision_list(context, data_dict):
    model = context["model"]
    id = data_dict["id"]
    pkg = model.Package.get(id)
    if pkg is None:
        raise NotFound
    check_access(pkg, model.Action.READ, context)

    revision_dicts = []
    for revision, object_revisions in pkg.all_related_revisions:
        revision_dicts.append(model.revision_as_dict(revision,
                                                     include_packages=False))
    return revision_dicts

def group_list(context, data_dict):
    model = context["model"]
    user = context["user"]
    api = context.get('api_version') or '1'
    ref_group_by = 'id' if api == '2' else 'name';

    query = ckan.authz.Authorizer().authorized_query(user, model.Group)
    groups = query.all() 
    return [getattr(p, ref_group_by) for p in groups]

def group_list_authz(context, data_dict):
    model = context['model']
    user = context['user']
    pkg = context.get('package')

    query = ckan.authz.Authorizer().authorized_query(user, model.Group, model.Action.EDIT)
    groups = set(query.all())
    return dict((group.id, group.name) for group in groups)

def group_list_availible(context, data_dict):
    model = context['model']
    user = context['user']
    pkg = context.get('package')

    query = ckan.authz.Authorizer().authorized_query(user, model.Group, model.Action.EDIT)
    groups = set(query.all())

    if pkg:
        groups = groups - set(pkg.groups)

    return [(group.id, group.name) for group in groups]

def licence_list(context, data_dict):
    model = context["model"]
    license_register = model.Package.get_license_register()
    licenses = license_register.values()
    licences = [l.as_dict() for l in licenses]
    return licences

def tag_list(context, data_dict):
    model = context['model']
    user = context['user']

    q = data_dict.get('q','')
    if q:
        limit = data_dict.get('limit',25)
        offset = data_dict.get('offset',0)
        return_objects = data_dict.get('return_objects',True)

        query = query_for(model.Tag, backend='sql')
        query.run(query=q,
                  limit=limit,
                  offset=offset,
                  return_objects=return_objects,
                  username=user)
        tags = query.results
    else:
        tags = model.Session.query(model.Tag).all() #TODO

    tag_list = [tag.name for tag in tags]
    return tag_list


def package_relationships_list(context, data_dict):

    ##TODO needs to work with dictization layer
    model = context['model']
    user = context['user']
    api = context.get('api_version') or '1'

    id = data_dict["id"]
    id2 = data_dict.get("id2")
    rel = data_dict.get("rel")
    ref_package_by = 'id' if api == '2' else 'name';
    pkg1 = model.Package.get(id)
    pkg2 = None
    if not pkg1:
        raise NotFound('First package named in request was not found.')
    if id2:
        pkg2 = model.Package.get(id2)
        if not pkg2:
            raise NotFound('Second package named in address was not found.')

    if rel == 'relationships':
        rel = None

    relationships = ckan.authz.Authorizer().\
                    authorized_package_relationships(\
                    user, pkg1, pkg2, rel, model.Action.READ)

    if rel and not relationships:
        raise NotFound('Relationship "%s %s %s" not found.'
                                 % (id, rel, id2))
    
    relationship_dicts = [rel.as_dict(pkg1, ref_package_by=ref_package_by) 
                          for rel in relationships]

    return relationship_dicts

def package_show(context, data_dict):

    model = context['model']
    api = context.get('api_version') or '1'
    id = data_dict['id']

    pkg = model.Package.get(id)

    context['package'] = pkg

    if pkg is None:
        raise NotFound
    check_access(pkg, model.Action.READ, context)

    package_dict = package_dictize(pkg, context)

    for item in PluginImplementations(IPackageController):
        item.read(pkg)

    return package_dict


def revision_show(context, data_dict):
    model = context['model']
    api = context.get('api_version') or '1'
    id = data_dict['id']
    ref_package_by = 'id' if api == '2' else 'name'

    rev = model.Session.query(model.Revision).get(id)
    if rev is None:
        raise NotFound
    rev_dict = model.revision_as_dict(rev, include_packages=True,
                                      ref_package_by=ref_package_by)
    return rev_dict

def group_show(context, data_dict):
    model = context['model']
    id = data_dict['id']
    api = context.get('api_version') or '1'


    group = model.Group.get(id)
    context['group'] = group

    if group is None:
        raise NotFound
    check_access(group, model.Action.READ, context)

    group_dict = group_dictize(group, context)

    for item in PluginImplementations(IGroupController):
        item.read(group)

    return group_dict


def tag_show(context, data_dict):
    model = context['model']
    api = context.get('api_version') or '1'
    id = data_dict['id']
    #ref_package_by = 'id' if api == '2' else 'name'

    tag = model.Tag.get(id) #TODO tags
    context['tag'] = tag

    if tag is None:
        raise NotFound

    tag_dict = tag_dictize(tag,context)
    extended_packages = []
    for package in tag_dict['packages']:
        extended_packages.append(_extend_package_dict(package,context))

    tag_dict['packages'] = extended_packages

    return tag_dict
    package_list = [getattr(pkgtag.package, ref_package_by)
                    for pkgtag in obj.package_tags]
    return package_list 


def package_show_rest(context, data_dict):

    package_show(context, data_dict)

    api = context.get('api_version') or '1'
    pkg = context['package']

    if api == '1':
        package_dict = package_to_api1(pkg, context)
    else:
        package_dict = package_to_api2(pkg, context)

    return package_dict

def group_show_rest(context, data_dict):

    group_show(context, data_dict)
    api = context.get('api_version') or '1'
    group = context['group']

    if api == '2':
        group_dict = group_to_api2(group, context)
    else:
        group_dict = group_to_api1(group, context)

    return group_dict

def tag_show_rest(context, data_dict):

    tag_show(context, data_dict)
    api = context.get('api_version') or '1'
    tag = context['tag']

    if api == '2':
        tag_dict = tag_to_api2(tag, context)
    else:
        tag_dict = tag_to_api1(tag, context)

    return tag_dict

def package_autocomplete(context, data_dict):
    '''Returns packages containing the provided string'''
    model = context['model']
    session = context['session']
    user = context['user']
    q = data_dict['q']

    like_q = u"%s%%" % q

    #TODO: Auth
    pkg_query = ckan.authz.Authorizer().authorized_query(user, model.Package)
    pkg_query = session.query(model.Package) \
                    .filter(or_(model.Package.name.ilike(like_q),
                                model.Package.title.ilike(like_q)))
    pkg_query = pkg_query.limit(10)

    pkg_list = []
    for package in pkg_query:
        result_dict = table_dictize(package, context)
        pkg_list.append(result_dict)

    return pkg_list

def package_search(context, data_dict):
    model = context['model']
    session = context['session']
    user = context['user']

    q=data_dict.get('q','')
    fields=data_dict.get('fields',[])
    facet_by=data_dict.get('facet_by',[])
    limit=data_dict.get('limit',20)
    offset=data_dict.get('offset',0)
    return_objects=data_dict.get('return_objects',False)
    filter_by_openness=data_dict.get('filter_by_openness',False)
    filter_by_downloadable=data_dict.get('filter_by_downloadable',False)

    query = query_for(model.Package)
    query.run(query=q,
              fields=fields,
              facet_by=facet_by,
              limit=limit,
              offset=offset,
              return_objects=return_objects,
              filter_by_openness=filter_by_openness,
              filter_by_downloadable=filter_by_downloadable,
              username=user)
    
    results = []
    for package in query.results:
        result_dict = table_dictize(package, context)
        result_dict = _extend_package_dict(result_dict,context)

        results.append(result_dict)

    return {
        'count': query.count,
        'facets': query.facets,
        'results': results
    }

def _extend_package_dict(package_dict,context):
    model = context['model']

    resources = model.Session.query(model.Resource)\
                .join(model.ResourceGroup)\
                .filter(model.ResourceGroup.package_id == package_dict['id'])\
                .all()
    if resources:
        package_dict['resources'] = resource_list_dictize(resources, context)
    else:
        package_dict['resources'] = []
    license_id = package_dict['license_id']
    if license_id:
        isopen = model.Package.get_license_register()[license_id].isopen()
        package_dict['isopen'] = isopen
    else:
        package_dict['isopen'] = False

    return package_dict
