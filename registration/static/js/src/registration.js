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

(function() {
'use strict';

// App configuration //////////////////////////////////////////////////////////

var app = angular.module('RegistrationApp', ['djng.forms']);

app.config(function($httpProvider) {
    $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
});


// Controllers ////////////////////////////////////////////////////////////////

app.controller('Registration', ['$scope', '$http', 'djangoForm', function($scope, $http, djangoForm) {

    // These fields will be validated on the server via ajax:
    // - Unique checks can only be done on the server.
    // - Password strength is validated on the server as the python and js
    //   versions of zxcvbn do not always give the same result.
    var serverValidationFields = [
        'subdomain',
        'username',
        'email',
        'password',
        'password_confirmation'
    ];

    // Returns a list of all form fields.
    var getFormFields = function() {
        return _.keys($scope.form).filter(key => !/^\$/.test(key));
    };

    // Returns a list of form field names that have been modified.
    var getModifiedFields = function() {
        return getFormFields().filter(key => $scope.form[key].$dirty || $scope.form[key].$message);
    };

    // Display the given error messages, making sure not to clear messages
    // that are already displayed.
    var displayErrors = function(errors) {
        errors = _.pick(errors, getModifiedFields());
        djangoForm.setErrors($scope.form, errors);
    };

    // Validate the registration form on the server.
    $scope.validate = _.debounce(function() {
        var params = {};
        getFormFields().forEach(function(key) {
            params[key] = $scope.form[key].$viewValue;
        });
        var request = $http.get('/api/v1/registration/register/validate/', {
            params: params
        });
        request.success(displayErrors);
        request.error(function() {
            console.error('Failed to validate form');
        });
    }, 500);

    // Trigger server-side validation.
    serverValidationFields.forEach(function(field) {
        $scope.$watch('registration.' + field, function() {
            var formField = $scope.form[field];
            if (formField && formField.$dirty) {
                $scope.validate();
            }
        });
    });

}]);

})();
