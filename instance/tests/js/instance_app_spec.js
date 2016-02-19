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

// Tests //////////////////////////////////////////////////////////////////////

describe('Instance app', function () {
    var httpBackend,
        indexController,
        instanceList,
        instanceDetail,
        OpenCraftAPI,
        $scope;

    beforeEach(function() {
        window.swampdragon = {
            onChannelMessage: jasmine.createSpy(),
            ready: jasmine.createSpy()
        };
        angular.mock.module('restangular');
        angular.mock.module('InstanceApp');
    });

    describe('Index controller', function() {
        beforeEach(inject(function($controller, _$httpBackend_, $rootScope, _OpenCraftAPI_) {
            $scope = $rootScope.$new();
            httpBackend = _$httpBackend_;
            OpenCraftAPI = _OpenCraftAPI_;

            // Models
            instanceList = jasmine.loadFixture('api/instances_list.json');
            instanceDetail = jasmine.loadFixture('api/instance_detail.json');
            httpBackend.whenGET('/api/v1/openedxinstance/').respond(instanceList);
            httpBackend.whenGET('/api/v1/openedxinstance/2/').respond(instanceDetail);

            indexController = $controller('Index', {$scope: $scope, OpenCraftAPI: OpenCraftAPI});
            httpBackend.flush(); // Clear calls from the controller init
        }));

        afterEach(function () {
            httpBackend.verifyNoOutstandingExpectation();
            httpBackend.verifyNoOutstandingRequest();
        });

        describe('$scope.select', function() {
            it('select the instance', function() {
                $scope.select({id: 2});
                httpBackend.flush();
                expect($scope.selected.instance.domain).toEqual('tmp.sandbox.opencraft.com');
            });
        });

        describe('$scope.updateInstanceList', function() {
            it('loads the instance list from the API on init', function() {
                expect(jasmine.sanitizeRestangularAll($scope.instanceList)).toEqual(instanceList);
            });

            it('sets $scope.loading while making the ajax call', function() {
                expect($scope.loading).not.toBeTruthy();
                $scope.updateInstanceList();
                expect($scope.loading).toBeTruthy();
                httpBackend.flush();
                expect($scope.loading).not.toBeTruthy();
            });

            it('updates the selected instance when updating the list', function() {
                instanceDetail.domain = 'old.example.com';
                $scope.select($scope.instanceList[0]);
                httpBackend.flush();
                expect($scope.selected.instance.domain).toEqual('old.example.com');

                instanceDetail.domain = 'tmp.sandbox.opencraft.com';
                $scope.updateInstanceList();
                httpBackend.flush();
                expect($scope.selected.instance.domain).toEqual('tmp.sandbox.opencraft.com');
            });
        });

        describe('$scope.provision', function() {
            it('notifies backend and changes status to terminating', function() {
                var instance = $scope.instanceList[0];
                expect(instance.active_server_set[0].status).toEqual('ready');
                httpBackend.expectPOST('/api/v1/openedxinstance/2/provision/').respond('');
                $scope.provision(instance);
                httpBackend.flush();
                expect(instance.active_server_set[0].status).toEqual('terminating');
            });
        });

        describe('$scope.handleChannelMessage', function() {
            it('server_update', function() {
                $scope.updateInstanceList = jasmine.createSpy();
                $scope.handleChannelMessage('notifier', {data: {type: 'server_update'}});
                expect($scope.updateInstanceList).toHaveBeenCalled();
            });

            it('instance_log', function() {
                $scope.select($scope.instanceList[0]);
                httpBackend.flush();
                var log_entry = {
                    level: 'INFO',
                    created: new Date(2015, 10, 4, 10, 45, 0),
                    text: '### Added via websocket ###'
                };
                expect($scope.selected.instance.log_entries).not.toContain(log_entry);
                $scope.handleChannelMessage('notifier', {data: {
                    type: 'instance_log',
                    instance_id: 2,
                    log_entry: log_entry
                }});
                expect($scope.selected.instance.log_entries).toContain(log_entry);
            });

            it('errors', function() {
                $scope.select($scope.instanceList[0]);
                httpBackend.flush();
                var log_entry_error = {
                    level: 'ERROR',
                    created: new Date(2015, 10, 4, 10, 45, 0),
                    text: '### Added via websocket ###'
                };
                $scope.handleChannelMessage('notifier', {data: {
                    type: 'instance_log',
                    instance_id: 2,
                    log_entry: log_entry_error
                }});
                var log_entry_info = {
                    level: 'INFO',
                    created: new Date(2015, 10, 4, 10, 45, 0),
                    text: '### Added via websocket ###'
                };
                $scope.handleChannelMessage('notifier', {data: {
                    type: 'instance_log',
                    instance_id: 2,
                    log_entry: log_entry_info
                }});
                expect($scope.selected.instance.log_error_entries).toContain(log_entry_error);
                expect($scope.selected.instance.log_error_entries).not.toContain(log_entry_info);
            });
        });
    });
});

})();
