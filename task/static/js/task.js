
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

        $scope.select = function(selectedType, selectedObject) {
            $scope.selected[selectedType] = selectedObject;
            console.log('Selected:', selectedType, selectedObject);
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
