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

app.config(function($stateProvider, $urlRouterProvider, RestangularProvider) {
    // For any unmatched url, send to /
    $urlRouterProvider.otherwise("/instances/");

    // Required by Django
    RestangularProvider.setRequestSuffix('/');

    $stateProvider
        .state('instances', {
            url: "/instances/",
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
            resolve: {
                // Load the instance before initializing this controller:
                instance: function(OpenCraftAPI, $stateParams) {
                    return OpenCraftAPI.one("instance", $stateParams.instanceId).get();
                },
            },
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
            $scope.selected = {};
            $scope.state = $state;

            $scope.instanceList = [];
            $scope.updateInstanceList();

            // Init websockets
            swampdragon.onChannelMessage($scope.handleChannelMessage);
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

                if($scope.selected.instance) {
                    $scope.select($scope.selected.instance);
                }
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

        $scope.handleChannelMessage = function(channels, message) {
            console.log('Received websocket message', channels, message.data);
            if(message.data.type === 'server_update') {
                $scope.updateInstanceList();
            }
        };

        $scope.init();
    }
]);


app.controller("Details", ['$scope', 'instance', '$state', '$stateParams', 'OpenCraftAPI',
    function ($scope, instance, $state, $stateParams, OpenCraftAPI) {

        $scope.init = function() {
            $scope.instance = instance;
            $scope.is_updating_from_pr = false;
            $scope.instance_active_tabs = {};
        };

        $scope.update_from_pr = function() {
            if ($scope.is_updating_from_pr) {
                throw "This instance is already being updated.";
            }
            if (!instance.source_pr) {
                throw "This instance is not associated with a PR.";
            }
            $scope.is_updating_from_pr = true; // Start animation to show that we're doing the update
            OpenCraftAPI.one('pr_watch', instance.source_pr.id).post('update_instance').then(function () {
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
            // Reload the instance data from the server.
            return OpenCraftAPI.one("instance", $stateParams.instanceId).get().then(function(instance) {
                $scope.instance = instance;
            });
        }

        $scope.provision = function(instance) {
            console.log('Provisioning instance', instance);
            var notification = function(response, fallback) {
                if (response && response.data) {
                    return response.data.status || fallback;
                }
                return fallback;
            };
            return instance.post('provision').then(function(response) {
                _.each(instance.active_server_set, function(server) {
                    if(server.status !== 'terminated') {
                        server.status = 'terminating';
                    }
                });
                $scope.notify(notification(response, 'Provisioning'));
            }, function(response) {
                $scope.notify(notification(response, 'Provisioning failed'), 'alert');
            });
        };

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
