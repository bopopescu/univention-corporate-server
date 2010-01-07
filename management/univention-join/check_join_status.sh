#!/bin/sh
#
# Univention Join
#  helper script: checks the join status of the local system
#
# Copyright (C) 2004-2010 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

LOG_FILE=/var/log/univention/check_join_status.log

log_error ()
{
	local message="Error: $1"
	echo $message
	echo $message >> $LOG_FILE
	exit 1
}
log_warn ()
{
	local message="Warning: $1"
	echo $message
	echo $message >> $LOG_FILE
}

echo "Start $0 at $(date)" >>$LOG_FILE
eval `univention-config-registry shell`

if [ ! -e /etc/machine.secret ]; then
	log_error "/etc/machine.secret not found"
fi

ldapsearch -x -h "$ldap_master" -D "$ldap_hostdn" -w `cat /etc/machine.secret` -b $ldap_base -s base >>$LOG_FILE 2>&1
if [ $? != 0 ]; then
	log_error "ldapsearch -x failed"
fi


ldapsearch -x -ZZ -h "$ldap_master" -D "$ldap_hostdn" -w `cat /etc/machine.secret` -b $ldap_base -s base >>$LOG_FILE 2>&1
if [ $? != 0 ]; then
	log_error "ldapsearch -x -ZZ failed"
fi

if [ ! -e /var/univention-join/joined ]; then
	log_error "The system isn't joined yet"
fi

ldapsearch -x -ZZ -D "$ldap_hostdn" -w `cat /etc/machine.secret` -b $ldap_base -s base >>$LOG_FILE 2>&1
if [ $? != 0 ]; then
	log_error "localhost ldapsearch failed"
fi

inst_files=`ls -l /usr/lib/univention-install/*.inst | wc -l`
configured=`wc -l /usr/lib/univention-install/.index.txt | awk '{print $1}'`

if [ $configured -lt $inst_files ]; then
	log_error "Not all install files configured"
fi

echo "Joined successful"
echo "Joined successfully" >> $LOG_FILE

exit 0
