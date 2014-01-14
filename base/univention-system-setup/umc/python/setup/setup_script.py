#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention System Setup
#  python setup script base
#
# Copyright 2012-2014 Univention GmbH
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
import os
import sys
from datetime import datetime

from univention.config_registry import ConfigRegistry
from univention.config_registry.frontend import ucr_update
from util import PATH_SETUP_SCRIPTS, PATH_PROFILE


def setup_i18n():
	import locale
	locale.setlocale(locale.LC_ALL, '')
	from univention.lib.i18n import Translation
	return Translation('univention-system-setup-scripts').translate
_ = setup_i18n()


class Profile(dict):
	def load(self, filename=PATH_PROFILE):
		with open(filename, 'r') as profile:
			for line in profile:
				line = line.strip()
				if not line:
					continue
				if line.startswith('#'):
					continue
				key, value = line.split('=', 1)
				for delim in ("'", '"'):
					if value.startswith(delim) and value.endswith(delim):
						value = value[1:-1]
						break
				self[key] = value

	def get_list(self, key, split_by=' '):
		'''
		Retrieve the value of var_name from the profile file.
		Return the string as a list split by split_by.
		'''
		value = self.get(key)
		return value.split(split_by) if value else []


class TransactionalUcr(object):
	def __init__(self):
		self.ucr = ConfigRegistry()
		self.ucr.load()
		self.changes = {}

	def set(self, key, value):
		'''
		Set the value of key of UCR.
		Does not save immediately.
		commit() is called at the end of inner_run(). If you need to commit
		changes immediately, you can call commit() at any time.
		'''
		orig_val = self.ucr.get(key)
		if orig_val == value:
			# in case it was overwritten previously
			self.changes.pop(key, None)
		else:
			self.changes[key] = value

	def commit(self):
		'''
		Saves UCR variables previously set by set_ucr_var(). Also commits
		changes (if done any). Is called automatically *if inner_run() did not
		raise an exception*. You can call it manually if you need to
		do it (e.g. in down()).
		'''
		if self.changes:
			ucr_update(self.ucr, self.changes)
			# reset (in case it is called multiple) times in a script
			self.changes.clear()

	def get(self, key, search_in_changes=True):
		'''
		Retrieve the value of key from ucr.
		If search_in_changes, it first looks in (not yet commited) values.
		'''
		if search_in_changes:
			try:
				return self.changes[key]
			except KeyError:
				pass
		return self.ucr.get(key)

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		if exc_type is None:
			self.commit()


class SetupScript(object):
	'''Baseclass for all Python-based Setup-Scripts.

	Script lifecycle:
	  __init__() -> up()
	  run() -> (inner_run() -> commit()) -> down()

	up(), (inner_run() -> commit), and down() and encapsulated by
	try-blocks, so the script should under no cirucumstances break.

	You should define name and script_name class (or instance) variables
	where name is localised and will show up at top of the progress and
	script_name is for logging and internal infos found at
	univention.management.console.modules.setup.util.ProgressParser.FRACTIONS.

	You should define your own inner_run-method, and, if needed,
	override (initially dummy) up() and down().

	You should execute a script like so:
	script = MySetupScript()
	script.run()
	Or maybe even better like so, as it calls sys.exit
	if __name__ == '__main__':
		script = MySetupScript()
		main(script) # helper function defined in here

	You may control the progress parser with these methods:
	self.header(msg) # automatically called by run()
	self.message(msg)
	self.error(msg)
	self.join_error(msg)
	self.steps(steps)
	self.step(step)
	'''
	name = ''

	def __init__(self, *args, **kwargs):
		'''Initialise Script. Will call self.up() with same *args
		and **kwargs as __init__() (which itself will leave them
		untouched)

		So dont override this method, instead write your own up().
		The default up()-method does nothing.

		self.up() is called in a try-except-block. If an exception
		was raised by up(), it will be saved and raised as soon as
		run() is called. You should make sure that this does not
		happen.
		'''
		self.ucr = TransactionalUcr()
		self._step = 1

		# remove script path from name
		self.script_name = os.path.abspath(sys.argv[0])
		if self.script_name.startswith(PATH_SETUP_SCRIPTS):
			self.script_name = self.script_name[len(PATH_SETUP_SCRIPTS):]

		self.profile = self.parse_profile()

		try:
			self.up(*args, **kwargs)
		except Exception as e:
			# save caught exception. raise later (in run())
			self._broken = e
		else:
			self._broken = False

	@staticmethod
	def parse_profile():
		profile = Profile()
		profile.load()
		return profile

	def inform_progress_parser(self, progress_attribute, msg):
		'''Internal method to inform progress parser.

		At the moment it writes info in a file which will be
		read by the parser. In a more advanced version, the script
		could change the state of the progress directly.
		'''
		msg = '__%s__:%s' % (progress_attribute.upper(), msg)
		if not msg.endswith('\n'):
			msg += '\n'
		sys.stdout.write(msg)
		sys.stdout.flush()

	def header(self, msg):
		'''Write header info of this script (for log file and parser).

		Called automatically by run(). Probably unneeded for developers
		'''
		print '===', self.script_name, datetime.now().strftime('(%Y-%m-%d %H:%M:%S)'), '==='
		self.inform_progress_parser('name', '%s %s' % (self.script_name, msg))

	def message(self, msg):
		'''Write a harmless __MSG__: for the parser
		'''
		self.inform_progress_parser('msg', msg)

	def error(self, msg):
		'''Write a non-critical __ERR__: for the parser
		The parser will save the error and inform the frontend
		that something went wrong
		'''
		self.inform_progress_parser('err', msg)

	def join_error(self, msg):
		'''Write a critical __JOINERR__: for the parser.
		The parser will save it and inform the frontend that something
		went terribly wrong leaving the system in an unjoined state
		'''
		self.inform_progress_parser('joinerr', msg)

	def steps(self, steps):
		'''Total number of __STEPS__: to come throughout the whole
		script. Progress within the script should be done with
		step() which is relative to steps()
		'''
		self.inform_progress_parser('steps', steps)

	def step(self, step=None):
		'''Inform parser that the next __STEP__: in this script
		was done. You can provide an exact number or None
		in which case an internal counter will be incremented
		'''
		if step is not None:
			self._step = step
		self.inform_progress_parser('step', self._step)
		self._step += 1

	def log(self, *msgs):
		'''Log messages in a log file'''
		print '### LOG ###'
		for msg in msgs:
			print msg,
		print

	def run(self):
		'''Run the SetupScript.
		Dont override this method, instead define your own
		inner_run()-method.

		Call self.header()
		If up() failed raise its exception.
		Run inner_run() in a try-except-block
		Return False if an exception occurred
		Otherwise return True/False depending on
		return code of inner_run itself.
		*In any case*, run self.down() in a try-except-block
		afterwards. If this should fail, return False.
		'''
		if self.name:
			self.header(self.name)
		try:
			if self._broken:
				raise self._broken
			else:
				success = self.inner_run()
				# is called only if inner_run
				# really returned and did not
				# raise an exception
				self.ucr.commit()
		except Exception as e:
			self.error(str(e))
			success = False
			import traceback
			self.log(traceback.format_exc(e))
		finally:
			try:
				self.down()
			except:
				success = False
		return success is not False

	def inner_run(self):
		'''Main function, called by run().
		Override this method in your SetupScriptClass.
		You may return True or False which will be propagated
		to run() itself. If you dont return False, True will be
		used implicitely.
		'''
		raise NotImplementedError('Define you own inner_run() method, please.')

	def up(self, *args, **kwargs):
		'''Override this method if needed.
		It is called during __init__ with the very same parameters
		as __init__ was called.
		'''
		pass

	def down(self):
		'''Override this method if needed.
		It is called at the end of run() even when an error in up()
		or inner_run() occurred.
		'''
		pass


from univention.lib.package_manager import PackageManager
from contextlib import contextmanager


class AptScript(SetupScript):
	'''More or less just a wrapper around
	univention.lib.package_manager.PackageManager
	with SetupScript capabilities.
	'''
	brutal_apt_options = True

	def up(self, *args, **kwargs):
		self.package_manager = PackageManager(
			info_handler=self.message,
			step_handler=self.step,
			error_handler=self.error,
			handle_only_frontend_errors=True, # ignore pmerror status
		)

		self.roles_package_map = {
			'domaincontroller_master' : 'univention-server-master',
			'domaincontroller_backup' : 'univention-server-backup',
			'domaincontroller_slave' : 'univention-server-slave',
			'memberserver' : 'univention-server-member',
			'fatclient' : 'univention-managed-client',
			'mobileclient' : 'univention-mobile-client',
		}
		self.current_server_role = self.ucr.get('server/role')
		self.wanted_server_role = self.profile.get('server/role')

	def set_always_install(self, *packages):
		self.package_manager.always_install(packages)

	@contextmanager
	def noninteractive(self):
		if self.brutal_apt_options:
			with self.package_manager.brutal_noninteractive():
				yield
		else:
			with self.package_manager.noninteractive():
				yield

	def update(self):
		with self.noninteractive():
			return self.package_manager.update()

	def get_package(self, pkg_name):
		return self.package_manager.get_package(pkg_name)

	def finish_task(self, *log_msgs):
		'''Task is finished. Increment counter and inform
		the progress parser. Reopen the cache (maybe unneeded
		but does not slow us down too much).
		'''
		# dont log msgs for now
		self.package_manager.add_hundred_percent()
		self.reopen_cache()

	def reopen_cache(self):
		self.package_manager.reopen_cache()

	def mark_auto(self, auto, *pkgs):
		self.package_manager.mark_auto(auto, *pkgs)

	def commit(self, install=None, remove=None, msg_if_failed=''):
		with self.noninteractive():
			self.package_manager.commit(install, remove, msg_if_failed=msg_if_failed)

	def install(self, *pkg_names):
		with self.noninteractive():
			self.package_manager.install(*pkg_names)

	def uninstall(self, *pkg_names):
		with self.noninteractive():
			self.package_manager.uninstall(*pkg_names)

	def get_package_for_role(self, role_name):
		'''Searches for the meta-package that belongs
		to the given role_name
		'''
		try:
			# get "real" package for server/role
			pkg_name = self.roles_package_map[role_name]
			return self.package_manager.cache[pkg_name]
		except KeyError:
			self.error(_('Failed to get package for Role %s') % role_name)
			return None

	def autoremove(self):
		with self.noninteractive():
			self.package_manager.autoremove()

	def down(self):
		self.package_manager.unlock()


def main(setup_script, exit=True):
	'''Helper function to run the setup_script and evaluate its
	return code as a "shell-compatible" one. You may sys.exit immediately
	'''
	success = setup_script.run()
	ret_code = 1 - int(success)
	if exit:
		sys.exit(ret_code)
	else:
		return ret_code
