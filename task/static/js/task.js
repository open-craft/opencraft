var app = angular.module('TaskApp', [
    'ngRoute',
    'ui.router',
    'restangular'
]);

app.config(function ($stateProvider, $urlRouterProvider, RestangularProvider) {
    // For any unmatched url, send to /
    $urlRouterProvider.otherwise("/task");

    $stateProvider
        .state('index', {
            url: "",
            templateUrl: "/static/html/partials/_task_list.html",
            controller: "TaskList"
        })
        .state('new', {
            url: "new",
            templateUrl: "/task/task-form",
            controller: "TaskFormCtrl"
        });
});

app.controller("TaskFormCtrl", ['$scope', 'Restangular', 'CbgenRestangular', '$q',
    function ($scope, Restangular, CbgenRestangular, $q) {


    }
]);
