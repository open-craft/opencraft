# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2019 OpenCraft <contact@opencraft.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

# Variables ###################################################################

GET = wget -qO
CDNJS = https://cdnjs.cloudflare.com/ajax/libs


# Files #######################################################################

all: font-awesome.min.css font-awesome.css.map

font-awesome.min.css:
	$(GET) $@ $(CDNJS)/font-awesome/4.4.0/css/font-awesome.min.css

font-awesome.css.map:
	$(GET) $@ $(CDNJS)/font-awesome/4.4.0/css/font-awesome.css.map
