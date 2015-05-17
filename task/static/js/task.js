var app = angular.module('TaskApp', [
    'ngRoute',
    'ui.router',
    'restangular'
]);

app.config(function($httpProvider) {
    $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
});

app.config(function($stateProvider, $urlRouterProvider, RestangularProvider) {
    // For any unmatched url, send to /
    $urlRouterProvider.otherwise("/task");

    $stateProvider
        .state('index', {
            url: "",
            templateUrl: "/static/html/task_list.html",
            controller: "TaskList"
        })
});

app.factory('OpenCraftAPI', function(Restangular) {
    return Restangular.withConfig(function(RestangularConfigurer) {
        RestangularConfigurer.setBaseUrl('/api/v1');
    });
});

app.controller("TaskList", ['$scope', 'Restangular', 'OpenCraftAPI', '$q',
    function ($scope, Restangular, OpenCraftAPI, $q) {
        
        OpenCraftAPI.all("task/").getList().then(function(taskList) {
            $scope.taskList = taskList;
        }, function(response) {
            console.log('Error from server: ', response);
        });
    }
]);
