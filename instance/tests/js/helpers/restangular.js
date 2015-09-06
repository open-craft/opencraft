// OpenCraft -- tools to aid developing and hosting free software projects
// Copyright (C) 2015 OpenCraft <xavier@opencraft.com>
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as
// published by the Free Software Foundation, either version 3 of the
// License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.

(function(){
"use strict";

// Functions //////////////////////////////////////////////////////////////////

// Helpers for testing restangular calls - https://github.com/mgonto/restangular/issues/98

// Remove all Restangular/AngularJS added methods in order to use Jasmine toEqual between the
// retrieved resource and the model
jasmine.sanitizeRestangularOne = function(item) {
    return _.omit(item, "route", "parentResource", "getList", "get", "post", "put", "remove",
                  "head", "trace", "options", "patch", "$get", "$save", "$query", "$remove",
                  "$delete", "$put", "$post", "$head", "$trace", "$options", "$patch", "$then",
                  "$resolved", "restangularCollection", "customOperation", "customGET",
                  "customPOST", "customPUT", "customDELETE", "customGETLIST", "$getList",
                  "$resolved", "restangularCollection", "one", "all", "doGET", "doPOST",
                  "doPUT", "doDELETE", "doGETLIST", "addRestangularMethod", "getRestangularUrl",
                  "getRequestedUrl", "clone", "reqParams", "withHttpConfig", "plain",
                  "restangularized", "several", "oneUrl", "allUrl", "fromServer",
                  "getParentList", "save");
};


// Apply "sanitizeRestangularOne" function to an array of items
jasmine.sanitizeRestangularAll = function(items) {
    return _.map(items, function(value, index) {
        return jasmine.sanitizeRestangularOne(value);
    });
};

})();
