// OpenCraft -- tools to aid developing and hosting free software projects
// Copyright (C) 2015-2019 OpenCraft <contact@opencraft.com>
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

// App configuration //////////////////////////////////////////////////////////

var app = angular.module('InstanceApp'); // Load the existing app so we can add to it.

app.config(function($stateProvider) {

    $stateProvider
        .state('instances.details.openedx_appserver_details', {
            url: 'edx-appserver/{appserverId:[0-9]+}/',
            templateUrl: "/static/html/instance/appserver.html",
            controller: "OpenEdXAppServerDetails",
        });
});

app.controller("OpenEdXAppServerDetails", ['$scope', '$state', '$stateParams', 'OpenCraftAPI',
    function ($scope, $state, $stateParams, OpenCraftAPI) {

        $scope.init = function() {
            $scope.appserver = null;
            $scope.appserverLogs = null; // Logs. Once loaded, this is {log_entries: [], log_error_entries: []}
            $scope.isFetchingLogs = false; // Are we currently loading the logs?
            $scope.logsPanelOpen = false; // Is the logs panel visible?
            $scope.refresh();
        };

        $scope.refresh = function() {
            return OpenCraftAPI.one("openedx_appserver", $stateParams.appserverId).get().then(function(appserver) {
                if (appserver.instance.id != $stateParams.instanceId) {
                    throw "This appserver is associated with another instance.";
                }
                $scope.appserver = appserver;
                $scope.is_active = appserver.is_active;
                $scope.is_running = appserver.status === 'running';
                $scope.vm_running = appserver.server.status === 'ready';
            }, function() {
                $scope.notify("Unable to load the appserver details.");
            });
        };

        $scope.fetchLogs = function() {
            if ($scope.appserverLogs || $scope.isFetchingLogs) {
                return;
            }
            $scope.isFetchingLogs = true;
            OpenCraftAPI.one("openedx_appserver", $stateParams.appserverId).customGET("logs").then(function(logs) {
                if (typeof logs.log_error_entries === "undefined") {
                    logs.log_error_entries = [];  // This field is not always present.
                }
                $scope.appserverLogs = logs;
                $scope.isFetchingLogs = false;
            }, function() {
                $scope.notify("Unable to load the logs for this appserver.");
                $scope.isFetchingLogs = false;
            });
        };

        $scope.$watch('logsPanelOpen', function(isOpen) {
            if (isOpen) {
                $scope.fetchLogs();
            }
        });

        $scope.terminate_appserver = function() {
            $scope.is_active = null; // Toggle all buttons off
            OpenCraftAPI.one("openedx_appserver", $stateParams.appserverId).post('terminate').then(function() {
                // Refresh the list of app servers in the instance scope, then refresh this appserver
                $scope.$parent.refresh().then(function() {
                    $scope.refresh();
                });
                $scope.notify($scope.appserver.name + ' is now being terminated');

            }, function() {
                $scope.refresh();
                $scope.notify('An error occurred. ' + $scope.appserver.name + ' could not be terminated.', 'alert');
            });
        };

        $scope.make_appserver_active = function(active) {
            var action = active ? 'active' : 'inactive';
            $scope.is_active = null; // Toggle all buttons off
            OpenCraftAPI.one("openedx_appserver", $stateParams.appserverId).post('make_' + action).then(function() {
                // Refresh the list of app servers in the instance scope, then refresh this appserver
                $scope.$parent.refresh().then(function() {
                    $scope.refresh();
                });
                $scope.notify($scope.appserver.name + ' is now ' + action +
                              '. The load balancer changes will take a short while to propagate.');

            }, function() {
                $scope.refresh();
                $scope.notify('An error occurred. ' + $scope.appserver.name + ' could not be made ' + action + '.',
                              'alert');
            });
        };
        $scope.$on("websocket:object_log_line", function(event, data){
            if (!$scope.appserverLogs) {
                return;
            }

            if (data.appserver_id == $scope.appserver.id || ($scope.appserver.server && data.server_id == $scope.appserver.server.id)) {
                if (data.log_entry.level == 'ERROR' || data.log_entry.level == 'CRITICAL') {
                    $scope.appserverLogs.log_error_entries.push(data.log_entry);
                }
                $scope.appserverLogs.log_entries.push(data.log_entry);
                $scope.$apply();
            }
        });

        $scope.$on("websocket:openedx_appserver_update", function(event, data){
           if (data.appserver_id == $scope.appserver.id) {
               $scope.refresh();
           }
        });

        $scope.init();
    }
]);

// This custom filter removes the prefix from log text:
// "instance.models.appserver | instance=60 (Instance),app_server=12 (AppServer 1) | "
app.filter('stripLogMeta', function() {
    return function(input) {
        return input.split(' | ').slice(2).join(' | ');
    };
});

// This custom filter pretty prints JSON structures from ansible output log.
app.filter('prettifyJSON', function() {
    return function(input) {
        var result = input;
        var trimmed = input.trim();
        // Checks for common ansible output patterns that may contain JSON data.
        var patterns = [
            / => ({[\s\S]*})$/,            // task result as an object
            / => \(item=({[\s\S]*})\)$/,   // item result as an object
            / => \(item=(\[[\s\S]*\])\)$/  // item result as an array
        ];
        for (var i = 0; i < patterns.length; i++) {
            var match = trimmed.match(patterns[i]);
            if (match) {
                try {
                    var json = JSON.parse(match[1]);
                    // stdout and stdout_lines contain the same data, except that stdout_lines is nicely
                    // broken by newlines while stdout is much less readable. Remove stdout if both are present.
                    if (json.hasOwnProperty('stdout') && json.hasOwnProperty('stdout_lines')) {
                        delete json.stdout;
                    }
                    // Do the same for stderr/stderr_lines
                    if (json.hasOwnProperty('stderr') && json.hasOwnProperty('stderr_lines')) {
                        delete json.stderr;
                    }
                    var pretty_printed = JSON.stringify(json, null, 4);
                    // Replace the matched portion with pretty-printed JSON.
                    result = result.replace(match[1], pretty_printed);
                    break;
                } catch (err) {
                    // ignore
                }
            }
        }
        return result;
    };
});

})();
