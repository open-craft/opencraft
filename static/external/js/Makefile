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

all: angular.min.js angular.min.js.map angular-mocks.js angular-route.min.js angular-route.min.js.map \
     angucomplete-alt.min.js angular-ui-router.min.js angular-sanitize.min.js \
     icheck.min.js jquery.min.js jshint.js marked.min.js restangular.min.js underscore-min.js \
     underscore-min.map zxcvbn.js

angular.min.js:
	$(GET) $@ $(CDNJS)/angular.js/1.4.6/angular.min.js

angular.min.js.map:
	$(GET) $@ $(CDNJS)/angular.js/1.4.6/angular.min.js.map

angucomplete-alt.min.js:
	$(GET) $@ $(CDNJS)/angucomplete-alt/3.0.0/angucomplete-alt.min.js

angular-mocks.js:
	$(GET) $@ $(CDNJS)/angular.js/1.4.6/angular-mocks.js

angular-route.min.js:
	$(GET) $@ $(CDNJS)/angular.js/1.4.6/angular-route.min.js

angular-sanitize.min.js:
	$(GET) $@ $(CDNJS)/angular.js/1.4.6/angular-sanitize.min.js

angular-route.min.js.map:
	$(GET) $@ $(CDNJS)/angular.js/1.4.6/angular-route.min.js.map

angular-ui-router.min.js:
	$(GET) $@ $(CDNJS)/angular-ui-router/0.2.15/angular-ui-router.min.js

icheck.min.js:
	$(GET) $@ https://github.com/fronteed/icheck/raw/6fd2ef473c16d74773bebb134d57621d877b140e/icheck.min.js

jquery.min.js:
	$(GET) $@ $(CDNJS)/jquery/2.1.4/jquery.min.js

jshint.js:
	$(GET) $@ $(CDNJS)/jshint/2.8.0/jshint.js

marked.min.js:
	$(GET) $@ $(CDNJS)/marked/1.1.0/marked.min.js

restangular.min.js:
	$(GET) $@ $(CDNJS)/restangular/1.5.1/restangular.min.js

underscore-min.js:
	$(GET) $@ $(CDNJS)/underscore.js/1.8.3/underscore-min.js

underscore-min.map:
	$(GET) $@ $(CDNJS)/underscore.js/1.8.3/underscore-min.map

zxcvbn.js:
	$(GET) $@ $(CDNJS)/zxcvbn/4.3.0/zxcvbn.js
