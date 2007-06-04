# Copyright (C) 2002-2003 Univention GmbH.
# licenses

import sys, string
sys.path=['.']+sys.path
import univention.admin.syntax
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

import univention.debug

translation=univention.admin.localization.translation('univention.admin.handlers.settings.umc')
_=translation.translate

module='settings/console_acl'
operations=['add','edit','remove','search','move']
superordinate='settings/cn'

childs=0
short_description=_('Settings: UMC ACLs')
long_description=_('List of ACLs for Univention Management Console')
options={
}
property_descriptions={
	'name': univention.admin.property(
			short_description=_('Name'),
			long_description=_('Name'),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=1,
		),
	'description': univention.admin.property(
			short_description=_('Description'),
			long_description=_('Description'),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			dontsearch=1,
			required=0,
			may_change=1,
			identifies=0,
		),
	'category': univention.admin.property(
			short_description=_('Category'),
			long_description=_('Console ACL Category'),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			dontsearch=1,
			required=0,
			may_change=1,
			identifies=0,
		),
	'hosts': univention.admin.property(
			short_description=_('Hosts'),
			long_description=_('Hosts or host group for this ACL'),
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			dontsearch=1,
			required=0,
			may_change=1,
			identifies=0,
		),
	'ldapbase': univention.admin.property(
			short_description=_('LDAP search base'),
			long_description=_('LDAP search base'),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			dontsearch=1,
			required=0,
			may_change=1,
			identifies=0,
		),
	'command': univention.admin.property(
			short_description=_('command'),
			long_description=_('Console command'),
			syntax=univention.admin.syntax.consoleOperations,
			multivalue=1,
			options=[],
			dontsearch=1,
			required=0,
			may_change=1,
			identifies=0,
		),
}

layout=[
	univention.admin.tab(_('General'),_('Package List'), [
		[univention.admin.field('name'), univention.admin.field('description') ],
		[univention.admin.field('category'), univention.admin.field('command')],
		[univention.admin.field('hosts'), univention.admin.field('ldapbase')],
	]),
]

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('category', 'univentionConsoleACLCategory', None, univention.admin.mapping.ListToString)
mapping.register('hosts', 'univentionConsoleACLHost', )
mapping.register('ldapbase', 'univentionConsoleACLBase', None, univention.admin.mapping.ListToString)
mapping.register('command', 'univentionConsoleACLCommand', None, univention.admin.mapping.ListToString)

class object(univention.admin.handlers.simpleLdap):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, arg=None):
		global mapping
		global property_descriptions

		self.co=co
		self.lo=lo
		self.dn=dn
		self.position=position
		self._exists=0
		self.mapping=mapping
		self.descriptions=property_descriptions

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate)

	def exists(self):
		return self._exists
	
	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('name'), mapping.mapValue('name', self.info['name']), self.position.getDn())

	def _ldap_addlist(self):
		return [ ('objectClass', ['top', 'univentionConsoleACL']) ]
	
def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionConsoleACL')
		])

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	try:
		for dn in lo.searchDn(unicode(filter), base, scope, unique, required, timeout, sizelimit):
			res.append(object(co, lo, None, dn))
	except:
		pass
	return res

def identify(dn, attr, canonical=0):
	return 'univentionConsoleACL' in attr.get('objectClass', [])
