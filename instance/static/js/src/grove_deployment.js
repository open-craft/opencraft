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

var app = angular.module('InstanceApp', []); // Load the existing app, so we can add to it.

app.config(function($stateProvider) {

    $stateProvider
        .state('instances.details.grove_deployment_details', {
            url: 'grove-deployments/{deploymentId:[0-9]+}/',
            templateUrl: "/static/html/instance/deployment.html",
            controller: "GroveDeploymentDetails",
        });
});

app.controller("GroveDeploymentDetails", ['$scope', '$state', '$stateParams', 'OpenCraftAPI',
    function ($scope, $state, $stateParams, OpenCraftAPI) {

        $scope.init = function() {
            $scope.deployment = null;
            $scope.refresh();
        };

        $scope.refresh = function() {
            return OpenCraftAPI.one("grove/deployments", $stateParams.deploymentId).get().then(function(deployment) {
                if (deployment.id != $stateParams.deploymentId || deployment.instance != $stateParams.instanceId) {
                    throw "This deployment is associated with another instance.";
                }
                $scope.deployment = deployment;
            }, function() {
                $scope.notify("Unable to load the appserver details.");
            });
        };

        $scope.init();
    }
]);

})();
