import datetime

from sqlalchemy import orm, types, Column, Table, ForeignKey, or_
import vdm.sqlalchemy

import meta
import core
import package as _package
import types as _types
import domain_object
import user as _user

__all__ = ['group_table', 'Group',
           'Member', 'GroupRevision', 'MemberRevision',
           'member_revision_table', 'member_table']

member_table = Table('member', meta.metadata,
                     Column('id', types.UnicodeText,
                            primary_key=True,
                            default=_types.make_uuid),
                     Column('table_name', types.UnicodeText,
                            nullable=False),
                     Column('table_id', types.UnicodeText,
                            nullable=False),
                     Column('capacity', types.UnicodeText,
                            nullable=False),
                     Column('group_id', types.UnicodeText,
                            ForeignKey('group.id')),)

vdm.sqlalchemy.make_table_stateful(member_table)
member_revision_table = core.make_revisioned_table(member_table)

group_table = Table('group', meta.metadata,
                    Column('id', types.UnicodeText,
                           primary_key=True,
                           default=_types.make_uuid),
                    Column('name', types.UnicodeText,
                           nullable=False, unique=True),
                    Column('title', types.UnicodeText),
                    Column('type', types.UnicodeText,
                           nullable=False),
                    Column('description', types.UnicodeText),
                    Column('image_url', types.UnicodeText),
                    Column('created', types.DateTime,
                           default=datetime.datetime.now),
                    Column('is_organization', types.Boolean, default=False),
                    Column('approval_status', types.UnicodeText,
                           default=u"approved"))

vdm.sqlalchemy.make_table_stateful(group_table)
group_revision_table = core.make_revisioned_table(group_table)


class Member(vdm.sqlalchemy.RevisionedObjectMixin,
             vdm.sqlalchemy.StatefulObjectMixin,
             domain_object.DomainObject):
    '''A Member object represents any other object being a 'member' of a
    particular Group.

    Meanings:
    * Package - the Group is a collection of Packages
                 - capacity is 'public', 'private'
                   or 'organization' if the Group is an Organization
                   (see ckan.logic.action.package_owner_org_update)
    * User - the User is granted permissions for the Group
                 - capacity is 'admin', 'editor' or 'member'
    * Group - the Group (Member.group_id) is a child of the Group (Member.id)
              in a hierarchy.
    '''
    def __init__(self, group=None, table_id=None, group_id=None,
                 table_name=None, capacity='public', state='active'):
        self.group = group
        self.group_id = group_id
        self.table_id = table_id
        self.table_name = table_name
        self.capacity = capacity
        self.state = state

    @classmethod
    def get(cls, reference):
        '''Returns a group object referenced by its id or name.'''
        query = meta.Session.query(cls).filter(cls.id == reference)
        member = query.first()
        if member is None:
            member = cls.by_name(reference)
        return member

    def get_related(self, type):
        """ TODO: Determine if this is useful
            Get all objects that are members of the group of the specified
            type.

            Should the type be used to get table_name or should we use the
            one in the constructor
        """
        pass

    def related_packages(self):
        # TODO do we want to return all related packages or certain ones?
        return meta.Session.query(_package.Package).filter_by(
            id=self.table_id).all()

    def __unicode__(self):
        # refer to objects by name, not ID, to help debugging
        if self.table_name == 'package':
            table_info = 'package=%s' % meta.Session.query(_package.Package).get(self.table_id).name
        elif self.table_name == 'group':
            table_info = 'group=%s' % meta.Session.query(Group).get(self.table_id).name
        else:
            table_info = 'table_name=%s table_id=%s' % (self.table_name, self.table_id)
        return u'<Member group=%s %s capacity=%s state=%s>' % \
               (self.group.name if self.group else repr(self.group),
                table_info, self.capacity, self.state)

class Group(vdm.sqlalchemy.RevisionedObjectMixin,
            vdm.sqlalchemy.StatefulObjectMixin,
            domain_object.DomainObject):

    def __init__(self, name=u'', title=u'', description=u'', image_url=u'',
                 type=u'group', approval_status=u'approved'):
        self.name = name
        self.title = title
        self.description = description
        self.image_url = image_url
        self.type = type
        self.approval_status = approval_status

    @property
    def display_name(self):
        if self.title is not None and len(self.title):
            return self.title
        else:
            return self.name

    @classmethod
    def get(cls, reference):
        '''Returns a group object referenced by its id or name.'''
        query = meta.Session.query(cls).filter(cls.id == reference)
        group = query.first()
        if group is None:
            group = cls.by_name(reference)
        return group
    # Todo: Make sure group names can't be changed to look like group IDs?

    @classmethod
    def all(cls, group_type=None, state=('active',)):
        """
        Returns all groups.
        """
        q = meta.Session.query(cls)
        if state:
            q = q.filter(cls.state.in_(state))

        if group_type:
            q = q.filter(cls.type == group_type)

        return q.order_by(cls.title)

    def set_approval_status(self, status):
        """
            Aproval status can be set on a group, where currently it does
            nothing other than act as an indication of whether it was
            approved or not. It may be that we want to tie the object
            status to the approval status
        """
        assert status in ["approved", "pending", "denied"]
        self.approval_status = status
        if status == "denied":
            pass

    def get_children_groups(self, type='group'):
        '''Returns the groups one level underneath this group in the hierarchy.
        Groups come in a list of dicts, each keyed by "id", "name" and "title".
        '''
        # The original intention of this method was to provide the full depth of
        # the tree, but the CTE was incorrect. This new query does what that old CTE
        # actually did, but is now far simpler.
        results =  meta.Session.query(Group.id, Group.name, Group.title).\
                     filter_by(type=type).\
                     join(Member, Member.table_id == Group.id).\
                     filter_by(group=self).\
                     filter_by(table_name='group').\
                     filter_by(state='active').\
                     all()

        return [{'id':id_, 'name': name, 'title': title}
                for id_, name, title in results]

    def get_children_group_hierarchy(self, type='group'):
        '''Returns the groups in all levels underneath this group in the hierarchy.
        The ordering is such that children always come after their parent.

        :rtype: a list of tuples, each one a Group and the ID its their parent
        group.

        e.g. >>> dept-health.get_children_group_hierarchy()
             [(<Group nhs>, u'8a163ba7-5146-4325-90c8-fe53b25e28d0'),
              (<Group wirral-ccg>, u'06e6dbf5-d801-40a1-9dc0-6785340b2ab4'),
              (<Group newport-ccg>, u'd2e25b41-720c-4ba7-bc8f-bb34b185b3dd')]
        '''
        results = meta.Session.query(Group, 'parent_id').\
            from_statement(HIERARCHY_DOWNWARDS_CTE).params(id=self.id, type=type).all()
        return results

    def get_parent_group_hierarchy(self, type='group'):
        '''Returns this group's parent, parent's parent, parent's parent's parent
        etc.. Sorted with the top level parent first.'''
        return meta.Session.query(Group).\
            from_statement(HIERARCHY_UPWARDS_CTE).params(id=self.id, type=type).all()

    @classmethod
    def get_top_level_groups(cls, type='group'):
        '''Returns a list of the groups (of the specified type) which have
        no parent groups. Groups are sorted by title.
        '''
        return meta.Session.query(cls).\
           outerjoin(Member, Member.table_id == Group.id and \
                     Member.table_name == 'group' and \
                     Member.state == 'active').\
           filter(Member.id==None).\
           filter(Group.type==type).\
           order_by(Group.title).all()

    def packages(self, with_private=False, limit=None,
            return_query=False, context=None):
        '''Return this group's active and pending packages.

        Returns all packages in this group with VDM revision state ACTIVE or
        PENDING.

        :param with_private: if True, include the group's private packages
        :type with_private: boolean

        :param limit: the maximum number of packages to return
        :type limit: int

        :param return_query: if True, return the SQLAlchemy query object
            instead of the list of Packages resulting from the query
        :type return_query: boolean

        :returns: a list of this group's packages
        :rtype: list of ckan.model.package.Package objects

        '''
        user_is_org_member = False
        context = context or {}
        user_is_admin = context.get('user_is_admin', False)
        user_id = context.get('user_id')
        if user_is_admin:
            user_is_org_member = True

        elif self.is_organization and user_id:
            query = meta.Session.query(Member) \
                    .filter(Member.state == 'active') \
                    .filter(Member.table_name == 'user') \
                    .filter(Member.group_id == self.id) \
                    .filter(Member.table_id == user_id)
            user_is_org_member = len(query.all()) != 0

        query = meta.Session.query(_package.Package).\
            filter(
                or_(_package.Package.state == vdm.sqlalchemy.State.ACTIVE,
                    _package.Package.state == vdm.sqlalchemy.State.PENDING)). \
            filter(group_table.c.id == self.id).\
            filter(member_table.c.state == 'active')

        # orgs do not show private datasets unless the user is a member
        if self.is_organization and not user_is_org_member:
            query = query.filter(_package.Package.private == False)
        # groups (not orgs) never show private datasets
        if not self.is_organization:
            query = query.filter(_package.Package.private == False)

        query = query.join(member_table,
                member_table.c.table_id == _package.Package.id)
        query = query.join(group_table,
                group_table.c.id == member_table.c.group_id)

        if limit is not None:
            query = query.limit(limit)

        if return_query:
            return query
        else:
            return query.all()

    @classmethod
    def search_by_name_or_title(cls, text_query, group_type=None, is_org=False):
        text_query = text_query.strip().lower()
        q = meta.Session.query(cls) \
            .filter(or_(cls.name.contains(text_query),
                        cls.title.ilike('%' + text_query + '%')))
        if is_org:
            q = q.filter(cls.type == 'organization')
        else:
            q = q.filter(cls.type != 'organization')
            if group_type:
                q = q.filter(cls.type == group_type)
        q = q.filter(cls.state == 'active')
        return q.order_by(cls.title)

    def add_package_by_name(self, package_name):
        if not package_name:
            return
        package = _package.Package.by_name(package_name)
        assert package
        if not package in self.packages():
            member = Member(group=self, table_id=package.id,
                            table_name='package')
            meta.Session.add(member)

    def get_groups(self, group_type=None, capacity=None):
        """ Get all groups that this group is within """
        import ckan.model as model
        # DR: Why is this cached? Surely the members can change in the
        #     lifetime of this Group?
        if '_groups' not in self.__dict__:
            self._groups = meta.Session.query(model.Group).\
                join(model.Member, model.Member.group_id == model.Group.id and
                     model.Member.table_name == 'group').\
                filter(model.Member.state == 'active').\
                filter(model.Member.table_id == self.id).all()

        groups = self._groups
        if group_type:
            groups = [g for g in groups if g.type == group_type]
        if capacity:
            groups = [g for g in groups if g.capacity == capacity]
        return groups

    @property
    def all_related_revisions(self):
        '''Returns chronological list of all object revisions related to
        this group. Ordered by most recent first.
        '''
        results = {}
        from group_extra import GroupExtra
        for grp_rev in self.all_revisions:
            if not grp_rev.revision in results:
                results[grp_rev.revision] = []
            results[grp_rev.revision].append(grp_rev)
        for class_ in [Member, GroupExtra]:
            rev_class = class_.__revision_class__
            obj_revisions = meta.Session.query(rev_class).\
                filter_by(group_id=self.id).all()
            for obj_rev in obj_revisions:
                if not obj_rev.revision in results:
                    results[obj_rev.revision] = []
                results[obj_rev.revision].append(obj_rev)
        result_list = results.items()
        ourcmp = lambda rev_tuple1, rev_tuple2: \
            cmp(rev_tuple2[0].timestamp, rev_tuple1[0].timestamp)
        return sorted(result_list, cmp=ourcmp)

    def __repr__(self):
        return '<Group %s>' % self.name


meta.mapper(Group, group_table,
            extension=[vdm.sqlalchemy.Revisioner(group_revision_table), ], )

vdm.sqlalchemy.modify_base_object_mapper(Group, core.Revision, core.State)
GroupRevision = vdm.sqlalchemy.create_object_version(meta.mapper, Group,
                                                     group_revision_table)

meta.mapper(Member, member_table, properties={
    'group': orm.relation(Group,
                          backref=orm.backref('member_all',
                                              cascade='all, delete-orphan')),
},
    extension=[vdm.sqlalchemy.Revisioner(member_revision_table), ],
)


vdm.sqlalchemy.modify_base_object_mapper(Member, core.Revision, core.State)
MemberRevision = vdm.sqlalchemy.create_object_version(meta.mapper, Member,
                                                      member_revision_table)

#TODO
MemberRevision.related_packages = lambda self: [self.continuity.package]



HIERARCHY_DOWNWARDS_CTE = """WITH RECURSIVE child AS
(
    -- non-recursive term
    SELECT * FROM member
    WHERE group_id = :id AND table_name = 'group' AND state = 'active'
    UNION ALL
    -- recursive term
    SELECT m.* FROM member AS m, child AS c
    WHERE m.group_id = c.table_id AND m.table_name = 'group'
          AND m.state = 'active'
)
SELECT G.*, child.group_id as parent_id FROM child
    INNER JOIN public.group G ON G.id = child.table_id
    WHERE G.type = :type AND G.state='active';"""

HIERARCHY_UPWARDS_CTE = """WITH RECURSIVE parenttree(depth) AS (
    -- non-recursive term
    SELECT 0, M.* FROM public.member AS M
    WHERE table_id = :id AND M.table_name = 'group' AND M.state = 'active'
    UNION
    -- recursive term
    SELECT PG.depth + 1, M.* FROM parenttree PG, public.member M
    WHERE PG.group_id = M.table_id AND M.table_name = 'group' AND M.state = 'active'
    )

SELECT G.*, PT.depth FROM parenttree AS PT
    INNER JOIN public.group G ON G.id = PT.group_id
    WHERE G.type = :type AND G.state='active'
    ORDER BY PT.depth DESC;"""
