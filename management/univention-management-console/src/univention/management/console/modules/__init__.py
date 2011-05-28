#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  Base class for UMC 2.0 modules
#
# Copyright 2006-2011 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

import notifier
import notifier.signals as signals

import univention.debug as ud

from ..protocol import Response
from ..protocol.definitions import *
from ..locales import Translation
from ..log import MODULE

_ = Translation( 'univention.management.console' ).translate

class Base( signals.Provider ):
	'''The base class for UMC modules of version 2 or higher'''
	def __init__( self ):
		signals.Provider.__init__( self )
		self.signal_new( 'success' )
		self.signal_new( 'failure' )
		self._username = None
		self._password = None
		self._sessionid = None
		self.__acls = None
		self.__requests = {}

	def _set_username( self, username ):
		self._username = username
	username = property( fset = _set_username )

	def _set_password( self, password ):
		self._password = password
	password = property( fset = _set_password )

	def _set_sessionid( self, sessionid ):
		self._sessionid = sessionid
	sessionid = property( fset = _set_sessionid )

	def _set_acls( self, acls ):
		self.__acls = acls
	acls = property( fset = _set_acls )

	def execute( self, method, object ):
		self.__requests[ object.id ] = ( object, method )

		MODULE.info( 'Executing %s' % str( object.arguments ) )
		try:
			func = getattr( self, method )
			func( object )
		except Exception, e:
			MODULE.error( 'Executing of %s has failed: %s' % ( method, str( e ) ) )
			import traceback

			res = Response( object )
			res.message = _( "Execution of command '%(command)s' has failed:\n\n%(text)s" ) % \
							{ 'command' : object.arguments[ 0 ], 'text' : unicode( traceback.format_exc() ) }
			MODULE.error( str( res.message ) )
			res.status = MODULE_ERR_COMMAND_FAILED
			self.signal_emit( 'failure', res )
			if object.id in self.__requests:
				del self.__requests[ object.id ]

	def permitted( self, command, options ):
		if not self.__acls:
			return False
		return self.__acls.is_command_allowed( command, options = options )

	def finished( self, id, response, message = None, success = True ):
		"""Should be invoked by module to finish the processing of a
		request. 'id' is the request command identifier, 'dialog' should
		contain the result as UMC dialog and 'success' defines if the
		request could be fulfilled or not. If there is a definition of a
		'_post' processing function it is called immediately."""

		if not id in self.__requests:
			return
		object, method = self.__requests[ id ]

		if not isinstance( response, Response ):
			res = Response( object )
			res.result = response
			res.message = message

		if not res.status:
			if success:
				res.status = SUCCESS
			else:
				res.status = MODULE_ERR

		self.result( res )

	def result( self, response ):
		if response.id in self.__requests:
			object, method = self.__requests[ response.id ]
			if response.status in ( SUCCESS, SUCCESS_MESSAGE, SUCCESS_PARTIAL, SUCCESS_SHUTDOWN ):
				response.module = [ 'ready' ]
				self.signal_emit( 'success', response )
			else:
				response.module = [ 'failure' ]
				self.signal_emit( 'failure', response )
			del self.__requests[ response.id ]


