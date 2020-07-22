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

var app = angular.module('InstanceApp', [
    'ngRoute',
    'ui.router',
    'restangular',
    'mm.foundation',
    'ngSanitize'
]);

app.config(function($httpProvider) {
    $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
});

app.config(function($stateProvider, $urlRouterProvider, RestangularProvider, $locationProvider) {
    // For any unmatched url, send to /
    $urlRouterProvider.otherwise('/');

    // Use History.pushState instead of hash/fragment URLs
    $locationProvider.html5Mode(true);

    // Required by Django
    RestangularProvider.setRequestSuffix('/');

    $stateProvider
        .state('instances', {
            url: "/",
            abstract: true, // By making this abstract, 'instances.empty' gets added to the homepage as well.
            templateUrl: "/static/html/instance/index.html",
            controller: "Index",
        })
        .state('instances.empty', {
            url: '',
            templateUrl: "/static/html/instance/empty.html",
            controller: "Empty",
        })
        .state('instances.details', {
            url: '{instanceId:[0-9]+}/',
            templateUrl: "/static/html/instance/details.html",
            controller: "Details",
        });
});


// Services
app.factory('OpenCraftAPI', function(Restangular) {
    return Restangular.withConfig(function(RestangularConfigurer) {
        RestangularConfigurer.setBaseUrl('/api/v1');
    });
});

app.factory('WebSocketClient', function() {
    var protocol = (window.location.protocol == 'https:') ? 'wss:' : 'ws:';
    return new WebSocket(protocol + '//' + window.location.host + '/ws/');
});

// Controllers ////////////////////////////////////////////////////////////////

app.controller("Index", ['$scope', '$state', 'OpenCraftAPI', 'WebSocketClient', '$timeout',
    function ($scope, $state, OpenCraftAPI, WebSocketClient, $timeout) {

        $scope.init = function() {
            $scope.loading = true;
            $scope.notification = null;
            $scope.state = $state;

            $scope.instanceList = [];
            $scope.updateInstanceList();
            $scope.webSocketMessageHandler = function(event) {
                let data = JSON.parse(event.data);
                let event_name = 'websocket:' + data.message.type;
                $scope.$broadcast(event_name, data.message);
            };
            $scope.webSocketErrorHandler = function(event) {
                console.error('Websocket connection closed unexpectedly')
            }
            WebSocketClient.onmessage = $scope.webSocketMessageHandler;
            WebSocketClient.onerror = $scope.webSocketErrorHandler;
        };

        $scope.updateInstanceList = function() {
            $scope.loading = true; // Display loading message

            console.log('Updating instance list');
            return OpenCraftAPI.all("instance").getList().then(function(instanceList) {
                $scope.instanceList = instanceList;
                console.log('Updated instance list:', instanceList);
            }, function(response) {
                console.log('Error from server: ', response);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        // Display a notification message for 10 seconds
        $scope.notify = function(message, type) {
            if ($scope.notification) {
                $timeout.cancel($scope.notification.timeout);
            }
            $scope.notification = {
                message: message,
                type: type,
                timeout: $timeout(function() {
                    $scope.notification = null;
                }, 10000)
            };
        };

        $scope.$on("websocket:instance_update", function(event, data) {
           $scope.updateInstanceList();
        });

        $scope.$on('websocket:openedx_appserver_update', function(event, data){
            $scope.updateInstanceList();
        })

        $scope.init();
    }
]);


app.controller("Details", ['$scope', '$state', '$stateParams', 'OpenCraftAPI',
    function ($scope, $state, $stateParams, OpenCraftAPI) {

        $scope.init = function() {
            $scope.is_spawning_appserver = false;
            $scope.is_updating_from_pr = false;
            $scope.instance_active_tabs = {};
            $scope.old_appserver_count = 0; // Remembers number of servers to detect when a new one appears

            $scope.instanceLogs = false;
            $scope.isFetchingLogs = false;

            $scope.isEditingNotes = false;
            $scope.originalNotes = "";
            $scope.showNotes = false;

            $scope.refresh();
        };

        $scope.update_from_pr = function() {
            if ($scope.is_updating_from_pr) {
                throw "This instance is already being updated.";
            }
            if (!$scope.instance.source_pr) {
                throw "This instance is not associated with a PR.";
            }
            $scope.is_updating_from_pr = true; // Start animation to show that we're doing the update
            OpenCraftAPI.one('pr_watch', $scope.instance.source_pr.id).post('update_instance').then(function () {
                $scope.notify('Instance settings updated.');
                $scope.is_updating_from_pr = false;
                $scope.refresh().then(function() {
                    // Switch to the settings tab to show the updated settings:
                    $scope.instance_active_tabs.settings_tab = true;
                });
            }, function() {
                $scope.notify('Update failed.', 'alert');
                $scope.is_updating_from_pr = false;
            });
        };

        $scope.editNotes = function() {
            let data = {"notes": $scope.instance.notes};
            OpenCraftAPI.one("instance", $scope.instance.id).customPOST(data, "set_notes").then(function () {
                $scope.notify('Instance notes updated.');
                $scope.refresh().then(function() {
                    $scope.isEditingNotes = false;
                });
            }, function() {
                $scope.notify('Update failed.', 'alert');
            });
        };

        $scope.cancelEditNotes = function() {
            $scope.instance.notes = $scope.originalNotes;
            $scope.isEditingNotes = false;
        };

        $scope.render = (text) => marked.parse(text);

        $scope.fetchLogs = function() {
            if ($scope.instanceLogs || $scope.isFetchingLogs) {
                return;
            }
            $scope.isFetchingLogs = true;
            OpenCraftAPI.one("instance", $scope.instance.id).customGET("logs").then(function(logs) {
                if (typeof logs.log_error_entries === "undefined") {
                    logs.log_error_entries = [];  // This field is not always present.
                }
                $scope.instanceLogs = logs;
                $scope.isFetchingLogs = false;
            }, function() {
                $scope.notify("Unable to load the logs for this appserver.");
                $scope.isFetchingLogs = false;
            });
        };

        $scope.$watch('instance_active_tabs.log_tab', function(tab_open){
            if (tab_open) {
                $scope.fetchLogs();
            }
        });

        $scope.loadAllAppServers = function() {
            OpenCraftAPI.one("instance", $scope.instance.id).customGET("app_servers").then(function(response) {
                $scope.instance.appservers = response.app_servers;
            }, function() {
                $scope.notify("Unable to load the app servers for this instance.");
            });
        };

        $scope.refresh = function() {
            // [Re]load the instance data from the server.
            return OpenCraftAPI.one("instance", $stateParams.instanceId).get().then(function(instance) {
                $scope.instance = instance;
                if (instance.appserver_count > $scope.old_appserver_count) {
                    // There is a new AppServer. If we were expecting one, it is here now.
                    // So stop animations and re-enable the "Launch new AppServer" button.
                    $scope.is_spawning_appserver = false;
                }
                $scope.old_appserver_count = instance.appserver_count;

                if ('notes' in $scope.instance) {
                    $scope.originalNotes = $scope.instance.notes;
                    $scope.showNotes = true;
                } else {
                    $scope.showNotes = false;
                }
            });
        };

        $scope.spawn_appserver = function() {
            console.log('Spawning new AppServer');
            $scope.is_spawning_appserver = true; // Disable the button

            OpenCraftAPI.all("openedx_appserver").post({instance_id: $stateParams.instanceId});
            // The API call above is an asynchronous task so it will return a 200 status immediately.
        };

        $scope.$on("websocket:instance_update", function(event, data){
           if (data.instance_id == $stateParams.instanceId) {
               $scope.refresh();
           }
        });

        $scope.$on("websocket:openedx_appserver_update", function(event, data){
            if (data.instance_id == $stateParams.instanceId) {
                $scope.refresh();
            }
        });

        $scope.$on('websocket:object_log_line', function(event, data){
            if (data.instance_id == $scope.instance.id && !data.appserver_id && $scope.instanceLogs) {
                $scope.instanceLogs.log_entries.push(data.log_entry);
            }
        })

        $scope.init();
    }
]);


app.controller("Empty", function ($scope) {
    // An important part of good UX is having a well-designed "empty state", which is what the user will first
    // see when they open your app. Here we put a nice greeting, based on the time of day.
    var hour = new Date().getHours();
    if (hour > 18) {
        $scope.greeting = "Good evening!";
    } else if (hour > 12) {
        $scope.greeting = "Good afternoon!";
    } else if (hour > 4) {
        $scope.greeting = "Good morning!";
    } else {
        $scope.greeting = "Working late, eh?";
    }
});

})();
