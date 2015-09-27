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

// Synchronously get a file via HTTP
jasmine.httpGET = function(path) {
    path = path + "?" + new Date().getTime();

    var xhr;
    try {
        xhr = new XMLHttpRequest();
        xhr.open("GET", path, false);
        xhr.send(null);
    } catch (e) {
        throw new Error("couldn't fetch " + path + ": " + e);
    }
    if (xhr.status < 200 || xhr.status > 299) {
        throw new Error("Could not load '" + path + "'.");
    }

    return xhr.responseText;
};

})();
