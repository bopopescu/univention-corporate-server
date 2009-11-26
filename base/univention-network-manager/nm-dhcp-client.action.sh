#!/bin/sh
#
# Univention Network Manager
#  script used by NM as dhclient script
#
# Copyright (C) 2009 Univention GmbH
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA	 02110-1301	 USA

if [ -z "$reason" -o $reason = "PREINIT" ]; then
        exit 0
fi

HOOKS_DIR=/etc/NetworkManager/dhcp-hooks.d/

# call hooks: each hook script might write shell script to standard output to change environment variables
for script in $(find ${HOOKS_DIR} -type f -name "*.py" -o -name "*.sh"); do
	eval $($script | egrep '(new_|old_|reason)')
done

# debugging
set | egrep '(new_|old_|reason)' > /tmp/nm-env
 
/usr/lib/NetworkManager/nm-dhcp-client.action.real

exit 0

	
