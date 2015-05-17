
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
        $scope.selectedTask = null;

        $scope.selectTask = function(task) {
            $scope.selectedTask = task;
            console.log('Selected task:', task);
        };
    }
]);

app.controller("TaskList", ['$scope', 'Restangular', 'OpenCraftAPI', '$q',
    function ($scope, Restangular, OpenCraftAPI, $q) {
        
        OpenCraftAPI.all("task/").getList().then(function(taskList) {
            $scope.taskList = taskList;
        }, function(response) {
            console.log('Error from server: ', response);
        });
    }
]);
