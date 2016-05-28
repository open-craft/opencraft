// OpenCraft -- tools to aid developing and hosting free software projects
// Copyright (C) 2015-2016 OpenCraft <contact@opencraft.com>
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
    'mm.foundation'
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


// Controllers ////////////////////////////////////////////////////////////////

app.controller("Index", ['$scope', '$state', 'OpenCraftAPI', '$timeout',
    function ($scope, $state, OpenCraftAPI, $timeout) {

        $scope.init = function() {
            $scope.loading = true;
            $scope.notification = null;
            $scope.state = $state;

            $scope.instanceList = [];
            $scope.updateInstanceList();

            // Init websockets
            swampdragon.onChannelMessage(function (channels, message) {
                // Broadcast sends a message to this scope and all child scopes:
                console.log('Received websocket message: ', message.data.type, message.data);
                $scope.$broadcast('swampdragon:' + message.data.type, message.data);
            });
            swampdragon.ready(function() {
                swampdragon.subscribe('notifier', 'notification', null);
                swampdragon.subscribe('notifier', 'log', null);
            });
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

        $scope.$on("swampdragon:instance_update", function (event, data) {
            $scope.updateInstanceList();
        });
        $scope.$on("swampdragon:openedx_appserver_update", function (event, data) {
            $scope.updateInstanceList();
        });

        $scope.init();
    }
]);


app.controller("Details", ['$scope', '$state', '$stateParams', 'OpenCraftAPI',
    function ($scope, $state, $stateParams, OpenCraftAPI) {

        $scope.init = function() {
            $scope.is_spawning_appserver = false;
            $scope.is_updating_from_pr = false;
            $scope.instance_active_tabs = {};
            $scope.old_appserver_count = 0;
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

        $scope.refresh = function() {
            // [Re]load the instance data from the server.
            return OpenCraftAPI.one("instance", $stateParams.instanceId).get().then(function(instance) {
                $scope.instance = instance;
                if (instance.appservers.length > $scope.old_appserver_count) {
                    // There is a new AppServer. If we were expecting one, it is here now.
                    // So stop animations and re-enable the "Launch new AppServer" button.
                    $scope.is_spawning_appserver = false;
                }
                $scope.old_appserver_count = instance.appservers.length;
            });
        };

        $scope.spawn_appserver = function() {
            console.log('Spawning new AppServer');
            $scope.is_spawning_appserver = true; // Disable the button

            OpenCraftAPI.all("openedx_appserver").post({instance_id: $stateParams.instanceId});
            // The API call above is an asynchronous task so it will return a 200 status immediately.
            // When the new app server is successfully created, it will send an openedx_appserver_update
            // notification, which will trigger $scope.refresh(), which will reset 'is_spawning_appserver'
        };

        $scope.$on("swampdragon:instance_update", function (event, data) {
            if (data.instance_id == $stateParams.instanceId) {
                $scope.refresh();
            }
        });
        $scope.$on("swampdragon:openedx_appserver_update", function(event, data) {
            // If the appserver belonged to this instance, refresh the display.
            if (data.instance_id == $stateParams.instanceId) {
                $scope.refresh();
            }
        });
        $scope.$on("swampdragon:object_log_line", function (event, data) {
            if (data.instance_id == $scope.instance.id && !data.appserver_id) {
                $scope.instance.log_entries.push(data.log_entry);
            }
        });

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
