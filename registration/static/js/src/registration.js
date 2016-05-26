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

// iCheck /////////////////////////////////////////////////////////////////////

// https://github.com/fronteed/iCheck/
$(document).ready(function() {
    $('input').icheck({
        checkboxClass: 'checkbox',
        hoverClass: 'checkbox--hover',
        focusClass: 'checkbox--focus',
        checkedClass: 'checkbox--checked',
        activeClass: 'checkbox--active',
        handle: 'checkbox'
    });
});


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
        return _.keys($scope.form).filter(function(key) {
            return !/^\$/.test(key);
        });
    };

    // Display the given error messages. Due to bugs in django-angular, we must
    // ensure that only modified fields that have passed client-side validation
    // and fields with a $message (i.e.  fields that have already been passed
    // to setErrors) are passed to setErrors.
    // https://github.com/jrief/django-angular/pull/260
    var displayErrors = function(errors) {
        var fields = getFormFields().filter(function(key) {
            var field = $scope.form[key];
            return field.$message || (field.$dirty && field.$valid);
        });
        errors = _.pick(errors, fields);
        djangoForm.setErrors($scope.form, errors);
    };

    // Validate the registration form on the server.
    $scope.validate = function() {
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
    };

    // Trigger server-side validation.
    serverValidationFields.forEach(function(field) {
        $scope.$watch('registration.' + field, _.debounce(function() {
            var formField = $scope.form[field];
            if (formField && formField.$dirty && formField.$valid) {
                $scope.validate();
            }
        }, 500));
    });

}]);

})();
