#!/usr/bin/python -u
# -*- coding: utf-8 -*-
# Pete Version Control Jabber roBot
#
# (C) Copyright 2004 Piotr Kontek <pete@chrome.pl>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License Version
# 2.1 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

__revision__ = "$Rev: 5 $"

import sys
from vcjb import publish
if len(sys.argv) == 3:
    base_dir=sys.path[0]
    publish.publish(base_dir, sys.argv[1], sys.argv[2])
    
else:
    print 'Usage: python ' + sys.argv[0] + ' repository \'log info\''
