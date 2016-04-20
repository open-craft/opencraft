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
    $urlRouterProvider.otherwise("/");

    // Required by Django
    RestangularProvider.setRequestSuffix('/');

    $stateProvider
        .state('index', {
            url: "/",
            templateUrl: "/static/html/instance/index.html",
            controller: "Index"
        });
});


// Services
app.factory('OpenCraftAPI', function(Restangular) {
    return Restangular.withConfig(function(RestangularConfigurer) {
        RestangularConfigurer.setBaseUrl('/api/v1');
    });
});


// Controllers ////////////////////////////////////////////////////////////////

app.controller("Index", ['$scope', 'Restangular', 'OpenCraftAPI', '$q', '$timeout',
    function ($scope, Restangular, OpenCraftAPI, $q, $timeout) {

        $scope.init = function() {
            $scope.loading = true;
            $scope.notification = null;
            $scope.selected = {};

            $scope.updateInstanceList();

            // Init websockets
            swampdragon.onChannelMessage($scope.handleChannelMessage);
            swampdragon.ready(function() {
                swampdragon.subscribe('notifier', 'notification', null);
                swampdragon.subscribe('notifier', 'log', null);
            });
        };

        $scope.select = function(instance) {
            $scope.loading = true; // Display loading message
            console.log('Selected instance', instance.id);

            return OpenCraftAPI.one('openedxinstance', instance.id).get().then(function(instance) {
                console.log('Fetched instance', instance.id);
                $scope.selected.instance = instance;
            }, function(response) {
                console.log('Error from server: ', response);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        $scope.provision = function(instance) {
            console.log('Provisioning instance', instance);
            var notification = function(response, fallback) {
                if (response && response.data) {
                    return response.data.status || fallback;
                }
                return fallback;
            };
            return instance.post('provision').then(function(response) {
                instance.server_status = 'terminating';
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

        $scope.updateInstanceList = function() {
            $scope.loading = true; // Display loading message

            return OpenCraftAPI.all("openedxinstance").getList().then(function(instanceList) {
                console.log('Updating instance list', instanceList);
                $scope.instanceList = instanceList;

                if($scope.selected.instance) {
                    $scope.select($scope.selected.instance);
                }
            }, function(response) {
                console.log('Error from server: ', response);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        $scope.handleChannelMessage = function(channels, message) {
            console.log('Received websocket message', channels, message.data);

            if(message.data.type === 'server_update') {
                $scope.updateInstanceList();
            } else if(message.data.type === 'instance_log') {
                if($scope.selected.instance && $scope.selected.instance.id === message.data.instance_id) {
                    $scope.$apply(function(){
                        if (message.data.log_entry.level == 'ERROR' || message.data.log_entry.level == 'CRITICAL') {
                            $scope.selected.instance.log_error_entries.push(message.data.log_entry);
                        }
                        $scope.selected.instance.log_entries.push(message.data.log_entry);
                    });
                }
            }
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

        $scope.init();
    }
]);

})();
