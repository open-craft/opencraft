
// App configuration //////////////////////////////////////////////////////////

var app = angular.module('TaskApp', [
    'ngRoute',
    'ui.router',
    'restangular',
    'mm.foundation'
]);

app.config(function($httpProvider) {
    $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
});

app.config(function($stateProvider, $urlRouterProvider, RestangularProvider) {
    // For any unmatched url, send to /
    $urlRouterProvider.otherwise("/");

    $stateProvider
        .state('index', {
            url: "/",
            templateUrl: "/static/html/task/index.html",
            controller: "Index"
        })
});


// Services ///////////////////////////////////////////////////////////////////

app.factory('OpenCraftAPI', function(Restangular) {
    return Restangular.withConfig(function(RestangularConfigurer) {
        RestangularConfigurer.setBaseUrl('/api/v1');
    });
});


// Controllers ////////////////////////////////////////////////////////////////

app.controller("Index", ['$scope', 'Restangular', 'OpenCraftAPI', '$q',
    function ($scope, Restangular, OpenCraftAPI, $q) {
        $scope.selected = Array();

        $scope.select = function(organization, project, task) {
            $scope.selected.organization = organization;
            $scope.selected.project = project;
            $scope.selected.task = task;

            console.log('Selected organization:', organization);
            console.log('Selected project:', project);
            console.log('Selected task:', task);
        };
    }
]);

app.controller("OrganizationList", ['$scope', 'Restangular', 'OpenCraftAPI', '$q',
    function ($scope, Restangular, OpenCraftAPI, $q) {
        
        OpenCraftAPI.all("organization/").getList().then(function(organizationList) {
            $scope.organizationList = organizationList;
        }, function(response) {
            console.log('Error from server: ', response);
        });
    }
]);

app.controller("ProjectTaskList", ['$scope', 'Restangular', 'OpenCraftAPI', '$q',
    function ($scope, Restangular, OpenCraftAPI, $q) {
    }
]);
