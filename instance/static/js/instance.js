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
        })
});


// Services ///////////////////////////////////////////////////////////////////

app.factory('OpenCraftAPI', function(Restangular) {
    return Restangular.withConfig(function(RestangularConfigurer) {
        RestangularConfigurer.setBaseUrl('/api/v1');
    });
});


// Function ///////////////////////////////////////////////////////////////////

function updateInstanceList($scope, OpenCraftAPI) {
    OpenCraftAPI.all("openedxinstance").getList().then(function(instanceList) {
        console.log('Updating instance list', instanceList);
        $scope.instanceList = instanceList;

        if($scope.selected.instance){
            var updated_instance = null;
            _.each(instanceList, function(instance) {
                if(instance.id === $scope.selected.instance.id) {
                    updated_instance = instance;
                }
            });
            $scope.selected.instance = updated_instance;
        }
    }, function(response) {
        console.log('Error from server: ', response);
    });
}


// Controllers ////////////////////////////////////////////////////////////////

app.controller("Index", ['$scope', 'Restangular', 'OpenCraftAPI', '$q',
    function ($scope, Restangular, OpenCraftAPI, $q) {
        // Selection
        $scope.selected = Array();
        $scope.select = function(selection_type, value) {
            $scope.selected[selection_type] = value;
            console.log('Selected ' + selection_type + ':', value);
        };

        // Reprovisioning
        $scope.provision = function(instance) {
            console.log('Provisioning instance', instance);
            instance.status = 'terminating';
            _.each(instance.active_server_set, function(server) {
                if(server.status !== 'terminated') {
                    server.status = 'terminating';
                }
            });
            instance.post("provision");
        };

        // Retreive instance list
        updateInstanceList($scope, OpenCraftAPI);

        // Intialize websockets
        swampdragon.onChannelMessage(function(channels, message) {
            console.log('Received websocket message', channels, message.data);

            if(message.data.type === 'server_update') {
                updateInstanceList($scope, OpenCraftAPI);
            } else if(message.data.type === 'instance_log') {
                if($scope.selected.instance && $scope.selected.instance.id === message.data.instance_id) {
                    $scope.$apply(function(){
                        $scope.selected.instance.log_text += message.data.log_entry + '\n';
                    });
                }
            }
        });
        swampdragon.ready(function() {
            swampdragon.subscribe('notifier', 'notification', null);
            swampdragon.subscribe('notifier', 'log', null);
        });
    }
]);
