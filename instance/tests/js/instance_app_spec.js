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

// Tests //////////////////////////////////////////////////////////////////////

describe('Instance app', function () {
    var $controller,
        httpBackend,
        instanceList,
        OpenCraftAPI,
        rootScope,
        $timeout;

    beforeAll(function() {
        fixture.setBase('instance/tests/fixtures');
    });

    function sanitizeRestangularAll(items) {
        var all = _.map(items, function (item) {
            return sanitizeRestangularOne(item);
        });
        return sanitizeRestangularOne(all);
    }

    function sanitizeRestangularOne(item) {
        return _.omit(item, "route", "parentResource", "getList", "get", "post", "put", "remove", "head", "trace", "options", "patch",
            "$get", "$save", "$query", "$remove", "$delete", "$put", "$post", "$head", "$trace", "$options", "$patch",
            "$then", "$resolved", "restangularCollection", "customOperation", "customGET", "customPOST",
            "customPUT", "customDELETE", "customGETLIST", "$getList", "$resolved", "restangularCollection", "one", "all", "doGET", "doPOST",
            "doPUT", "doDELETE", "doGETLIST", "addRestangularMethod", "getRestangularUrl", "getRequestedUrl", "clone", "reqParams", "withHttpConfig",
            "plain", "restangularized", "several", "oneUrl", "allUrl", "fromServer", "save", "singleOne", "getParentList");
    }

    function flushHttpBackend() {
        // Convenience method since httpBackend.flush() seems to generate calls
        // to $timeout which also need to be flushed.
        httpBackend.flush();
        $timeout.flush();
    };

    function getBroadcastMessage(data) {
        // Convenience method to return the message in the appropriate structure for broadcast.
        return {
            data: JSON.stringify(
                {type: data.type, message: data}
            )
        };
    }

    beforeEach(function() {
        angular.mock.module('restangular');
        angular.mock.module('InstanceApp');
        inject(function(_$controller_, _$httpBackend_, $rootScope, _$timeout_, _OpenCraftAPI_) {
            $controller = _$controller_;
            rootScope = $rootScope.$new();
            httpBackend = _$httpBackend_;
            $timeout = _$timeout_;
            OpenCraftAPI = _OpenCraftAPI_;
        });

        // Models
        instanceList = fixture.load('api/instances_list.json');
        httpBackend.whenGET('/api/v1/instance/').respond(instanceList);

        // Templates
        const templatePattern = /\/static\/html\/instance\/(.+)/;
        httpBackend.whenGET(templatePattern).respond(function(method, url, data) {
            const templateName = url.match(templatePattern)[1];
            const templateHTML = window.__html__[templateName];
            return [200, templateHTML];
        });

        // Instance controller
        const indexController = $controller('Index', {$scope: rootScope});
        flushHttpBackend(); // Clear calls from the controller init
    });

    afterEach(function () {
        httpBackend.verifyNoOutstandingExpectation();
        httpBackend.verifyNoOutstandingRequest();
        $timeout.verifyNoPendingTasks();
        fixture.cleanup();
    });


    describe('Index controller', function() {
        var $scope;
        beforeEach(function() {
            $scope = rootScope;
        });

        describe('$scope.init', function() {
            it('broadcasts websocket events to the current scope and all the child scopes', function() {
                const handler = jasmine.createSpy('Mock event handler');
                $scope.$on('websocket:test_event', handler);
                $scope.webSocketMessageHandler(getBroadcastMessage({otherVal: 42, type: 'test_event'}));
                expect(handler).toHaveBeenCalledWith(jasmine.any(Object), {'type': 'test_event', otherVal: 42});
            });
        });

        describe('$scope.updateInstanceList', function() {
            it('loads the instance list from the API on init', function() {
                expect($scope.instanceList.length).toEqual(instanceList.length);
                for (var i; i < $scope.instanceList.length; i++){
                    expect($scope.instanceList[i]).toEqual(instanceList[i]);
                }
            });

            it('sets $scope.loading while making the ajax call', function() {
                expect($scope.loading).not.toBeTruthy();
                $scope.updateInstanceList();
                expect($scope.loading).toBeTruthy();
                flushHttpBackend(); // Clear timeouts created by httpBackend
                expect($scope.loading).not.toBeTruthy();
            });
        });

        describe('websocket events', function() {
            beforeEach(function() {
                spyOn($scope, 'updateInstanceList');
            });
            it('update the instance list whenever an instance is updated', function() {
                $scope.webSocketMessageHandler(getBroadcastMessage({type: 'instance_update'}));
                expect($scope.updateInstanceList).toHaveBeenCalled();
            });
            it('update the instance list whenever an AppServer is updated', function() {
                $scope.webSocketMessageHandler(getBroadcastMessage({type: 'openedx_appserver_update'}));
                expect($scope.updateInstanceList).toHaveBeenCalled();
            });
            it('do not update the instance list for other changes', function() {
                $scope.webSocketMessageHandler(getBroadcastMessage({type: 'other_event'}));
                expect($scope.updateInstanceList).not.toHaveBeenCalled();
            });
        });

        describe('$scope.notify', function() {
            it('can be called to show temporary notifications', function() {
                expect($scope.notification).toBe(null);
                $scope.notify('Update failed.', 'alert');
                expect($scope.notification.message).toEqual('Update failed.');
                expect($scope.notification.type).toEqual('alert');
                $timeout.flush();
                expect($scope.notification).toBe(null);
            });
        });
    });


    describe('Instance Details controller', function() {
        var $scope,
            instanceDetail;

        beforeEach(function() {
            // Models
            instanceDetail = fixture.load('api/instance_detail.json');
            httpBackend.whenGET('/api/v1/instance/50/').respond(instanceDetail);

            $scope = rootScope.$new();
            const detailsController = $controller('Details', {$scope: $scope, $stateParams: {instanceId: 50}});
            flushHttpBackend(); // Clear calls from the controller init
        });

        describe('$scope.refresh', function() {
            it('loads the instance details from the API on init', function() {
                expect(sanitizeRestangularOne($scope.instance)).toEqual(instanceDetail);
            });
        });

        describe('websocket event handlers', function() {
            beforeEach(function() {
                spyOn(rootScope, 'updateInstanceList');
                spyOn($scope, 'refresh');
                $scope.instanceLogs = {'log_entries': []};
                spyOn($scope.instanceLogs.log_entries, 'push');
                console.log(typeof($scope.instanceLogs.log_entries.push));

            });
            it('update the instance details whenever the instance is updated', function() {
                $scope.webSocketMessageHandler(getBroadcastMessage({type: "instance_update", instance_id: 400}));
                expect($scope.refresh).not.toHaveBeenCalled();
                $scope.webSocketMessageHandler(getBroadcastMessage({type: "instance_update", instance_id: instanceDetail.id}));
                expect($scope.refresh).toHaveBeenCalled();
            });
            it("update the instance list whenever one of the instance's AppServers are updated", function() {
                $scope.webSocketMessageHandler(getBroadcastMessage({type: "openedx_appserver_update", instance_id: 400}));
                expect($scope.refresh).not.toHaveBeenCalled();
                $scope.webSocketMessageHandler(getBroadcastMessage({type: "openedx_appserver_update", instance_id: instanceDetail.id}));
                expect($scope.refresh).toHaveBeenCalled();
            });
            it("update the instance's log entries", function() {
                const logEntry = {created: new Date().toISOString(), level: "INFO", text: "A long time ago"};
                $scope.webSocketMessageHandler(getBroadcastMessage({
                    type: "object_log_line",
                    instance_id: instanceDetail.id,
                    log_entry: logEntry,
                }));
                expect($scope.refresh).not.toHaveBeenCalled();
                expect($scope.instanceLogs.log_entries.push).toHaveBeenCalledWith(logEntry);
            });
            it("do not update the instance's log entries for other instance logs", function() {
                $scope.webSocketMessageHandler(getBroadcastMessage({
                    type: "object_log_line",
                    instance_id: 400,
                    log_entry: {created: new Date(), level: "INFO", text: "Irrelevant log line"},
                }));
                expect($scope.refresh).not.toHaveBeenCalled();
                expect($scope.instanceLogs.log_entries.push).not.toHaveBeenCalled();
            });
            it("do not update the instance's log entries for AppServer logs", function() {
                $scope.webSocketMessageHandler(getBroadcastMessage({
                    type: "object_log_line",
                    instance_id: instanceDetail.id,
                    appserver_id: 15,
                    log_entry: {created: new Date(), level: "INFO", text: "Irrelevant log line"},
                }));
                expect($scope.refresh).not.toHaveBeenCalled();
                expect($scope.instanceLogs.log_entries.push).not.toHaveBeenCalled();
            });
            it('do not update the instance details for other changes', function() {
                $scope.webSocketMessageHandler(getBroadcastMessage({type: "other_update"}));
                expect($scope.refresh).not.toHaveBeenCalled();
            });
        });
        describe('$scope.spawn_appserver', function() {
            it('will spawn an appserver and set is_spawning_appserver=true until the appserver is ready', function() {
                expect($scope.is_spawning_appserver).toBe(false);
                httpBackend.expectPOST('/api/v1/openedx_appserver/', {instance_id: instanceDetail.id}).respond('');
                // Note: The API call above is an asynchronous task so it will return a 200 status immediately.
                $scope.spawn_appserver();
                expect($scope.is_spawning_appserver).toBe(true);
                flushHttpBackend();
                expect($scope.is_spawning_appserver).toBe(true);

                // Mock an unrelated update to an older AppServer, which should have no effect on is_spawning_appserver:
                $scope.webSocketMessageHandler(getBroadcastMessage(
                    {type: "openedx_appserver_update", instance_id: instanceDetail.id}
                ));
                flushHttpBackend();
                expect($scope.is_spawning_appserver).toBe(true);
                // Now, mock the result of successfully spawning an AppServer:
                const mockAppServer = {"id": 8, };
                instanceDetail.newest_appserver = mockAppServer;
                instanceDetail.appservers.push(mockAppServer);
                instanceDetail.appserver_count = instanceDetail.appservers.length;
                $scope.webSocketMessageHandler(getBroadcastMessage(
                    {type: "openedx_appserver_update", instance_id: instanceDetail.id}
                ));
                flushHttpBackend();
                expect($scope.is_spawning_appserver).toBe(false);
            });
        });

        describe('$scope.update_from_pr', function() {
            beforeEach(function() {
                spyOn(rootScope, 'notify');
                spyOn($scope, 'refresh').and.callThrough();
            });
            it('throws an exception if the instance is already updating from a PR', function() {
                expect($scope.is_updating_from_pr).toBe(false);
                $scope.is_updating_from_pr = true;
                expect($scope.update_from_pr).toThrow();
            });
            it('throws an exception if the instance is not associated with a PR', function() {
                delete $scope.instance.source_pr;
                expect($scope.is_updating_from_pr).toBe(false);
                expect($scope.update_from_pr).toThrow();
            });
            it('uses the API to update the instance settings from the PR', function() {
                expect($scope.is_updating_from_pr).toBe(false);
                expect($scope.instance_active_tabs.settings_tab).toBe(undefined);
                expect($scope.notify).not.toHaveBeenCalled();

                httpBackend.expectPOST('/api/v1/pr_watch/' + instanceDetail.source_pr.id + '/update_instance/').respond('');
                $scope.update_from_pr();
                expect($scope.is_updating_from_pr).toBe(true);
                expect($scope.refresh).not.toHaveBeenCalled();
                flushHttpBackend();
                expect($scope.is_updating_from_pr).toBe(false);
                expect($scope.notify).toHaveBeenCalledWith('Instance settings updated.');
                // Then the code should call refresh(), then switch to the "Settings" tab after the refresh completes:
                expect($scope.refresh).toHaveBeenCalled();
                expect($scope.instance_active_tabs.settings_tab).toBe(true);
            });
            it('shows an error message when unable to update the instance settings from the PR', function() {
                expect($scope.is_updating_from_pr).toBe(false);
                expect($scope.notify).not.toHaveBeenCalled();
                httpBackend.expectPOST('/api/v1/pr_watch/' + instanceDetail.source_pr.id + '/update_instance/').respond(500, '');
                $scope.update_from_pr();
                expect($scope.is_updating_from_pr).toBe(true);
                flushHttpBackend();
                expect($scope.is_updating_from_pr).toBe(false);
                expect($scope.notify).toHaveBeenCalledWith('Update failed.', 'alert');
                expect($scope.refresh).not.toHaveBeenCalled();
            });
        });
    });


    describe('OpenEdXAppServerDetails controller', function() {
        var $scope,
            parentScope,
            appServerDetail;

        beforeEach(function() {
            // Models
            appServerDetail = fixture.load('api/appserver_detail.json');
            httpBackend.whenGET('/api/v1/openedx_appserver/8/').respond(appServerDetail);

            // Mock the parent scope (instance details)
            parentScope = rootScope.$new(); // Scope for the Instance "Details" controller
            parentScope.instance = fixture.load('api/instance_detail.json');
            inject(function($q) {
                // Mock tthe instance refresh() method and make sure to return a promise.
                parentScope.refresh = jasmine.createSpy('Instance refresh method').and.returnValue($q.when({}));
            });

            // Create the controller and its scope:
            $scope = parentScope.$new();
            const stateParams = {
                instanceId: 50,
                appserverId: 8,
            }
            $controller('OpenEdXAppServerDetails', {$scope: $scope, $stateParams: stateParams});
            flushHttpBackend(); // Clear calls from the controller init
        });

        describe('$scope.refresh', function() {
            it('loads the AppServer details from the API on init', function() {
                expect(sanitizeRestangularOne($scope.appserver)).toEqual(appServerDetail);
            });
            it('sets is_active correctly', function() {
                expect($scope.is_active).toBe(true); // Based on the fixture, AppServer 8 is active

                appServerDetail.is_active = false;
                $scope.refresh();
                flushHttpBackend();
                expect($scope.is_active).toBeFalsy();

                appServerDetail.id = 404;
                $scope.refresh();
                flushHttpBackend();
                expect($scope.is_active).toBeFalsy();
            });
        });

        describe('loading log files', function() {
            it('loads the AppServer logs when the log panel is opened', function() {
                var logEntry = {
                    "level": "INFO",
                    "text": "instance.models.appserver | instance=50 (PR#12338: WIP S),app_server=8 (AppServer 2) | Starting provisioning",
                    "created": "2016-05-19T03:33:25.272824Z"
                };
                httpBackend.whenGET('/api/v1/openedx_appserver/8/logs/').respond({
                    "log_entries": [logEntry]
                });

                expect($scope.appserverLogs).toBe(null);
                $scope.logsPanelOpen = true;
                flushHttpBackend();
                expect($scope.appserverLogs.log_entries[0]).toEqual(logEntry);
            });
        });

        describe('$scope.make_appserver_active(true)', function() {
            it('will make an API call to make the AppServer active, then refresh the view', function() {
                appServerDetail.is_active = false;
                $scope.refresh();
                spyOn(rootScope, 'notify');
                spyOn($scope, 'refresh');
                httpBackend.expectPOST('/api/v1/openedx_appserver/' + appServerDetail.id + '/make_active/').respond('');
                $scope.make_appserver_active(true);
                flushHttpBackend();
                expect(parentScope.refresh).toHaveBeenCalled();
                expect($scope.refresh).toHaveBeenCalled();
                expect(rootScope.notify).toHaveBeenCalledWith('AppServer 2 is now active. The load balancer changes will take a short while to propagate.');
            });
            it('displays a notification if the AppServer failed to activate', function() {
                appServerDetail.is_active = false;
                $scope.refresh();
                spyOn(rootScope, 'notify');
                spyOn($scope, 'refresh');
                httpBackend.expectPOST('/api/v1/openedx_appserver/' + appServerDetail.id + '/make_active/').respond(500, '');
                $scope.make_appserver_active(true);
                flushHttpBackend();
                expect(parentScope.refresh).not.toHaveBeenCalled();
                expect($scope.refresh).toHaveBeenCalled();
                expect(rootScope.notify).toHaveBeenCalledWith('An error occurred. AppServer 2 could not be made active.', 'alert');
            });
        });

        describe('$scope.make_appserver_active(false)', function() {
            it('will make an API call to make the AppServer inactive, then refresh the view', function() {
                spyOn(rootScope, 'notify');
                spyOn($scope, 'refresh');
                httpBackend.expectPOST('/api/v1/openedx_appserver/' + appServerDetail.id + '/make_inactive/').respond('');
                $scope.make_appserver_active(false);
                flushHttpBackend();
                expect(parentScope.refresh).toHaveBeenCalled();
                expect($scope.refresh).toHaveBeenCalled();
                expect(rootScope.notify).toHaveBeenCalledWith('AppServer 2 is now inactive. The load balancer changes will take a short while to propagate.');
            });
            it('displays a notification if the AppServer failed to activate', function() {
                spyOn(rootScope, 'notify');
                spyOn($scope, 'refresh');
                httpBackend.expectPOST('/api/v1/openedx_appserver/' + appServerDetail.id + '/make_inactive/').respond(500, '');
                $scope.make_appserver_active(false);
                flushHttpBackend();
                expect(parentScope.refresh).not.toHaveBeenCalled();
                expect($scope.refresh).toHaveBeenCalled();
                expect(rootScope.notify).toHaveBeenCalledWith('An error occurred. AppServer 2 could not be made inactive.', 'alert');
            });
        });
        describe('websocket event handlers', function() {
            beforeEach(function() {
                spyOn(rootScope, 'updateInstanceList'); // Mock this out to avoid its HTTP requests
                spyOn($scope, 'refresh');
                $scope.appserverLogs = {log_entries: [], log_error_entries: []}; // Mock the loading of the logs
                spyOn($scope.appserverLogs.log_entries, 'push');
                spyOn($scope.appserverLogs.log_error_entries, 'push');
            });
            it('update the AppServer details whenever the AppServer is updated', function() {
                $scope.webSocketMessageHandler(getBroadcastMessage({type: "openedx_appserver_update", appserver_id: 404}));
                expect($scope.refresh).not.toHaveBeenCalled();
                $scope.webSocketMessageHandler(getBroadcastMessage({type: "openedx_appserver_update", appserver_id: appServerDetail.id}));
                expect($scope.refresh).toHaveBeenCalled();
            });
            it("update the AppServer's log entries for new AppServer logs", function() {
                const logEntry = {created: new Date().toISOString(), level: "INFO", text: "A long time ago"};
                $scope.webSocketMessageHandler(getBroadcastMessage({
                    type: "object_log_line",
                    appserver_id: appServerDetail.id,
                    log_entry: logEntry,
                }));
                expect($scope.refresh).not.toHaveBeenCalled();
                expect($scope.appserverLogs.log_entries.push).toHaveBeenCalledWith(logEntry);
                expect($scope.appserverLogs.log_error_entries.push).not.toHaveBeenCalled();
            });
            it("update the AppServer's log entries for new AppServer error logs", function() {
                const logEntry = {created: new Date().toISOString(), level: "ERROR", text: "Something went wrong"};
                $scope.webSocketMessageHandler(getBroadcastMessage({
                    type: "object_log_line",
                    appserver_id: appServerDetail.id,
                    log_entry: logEntry,
                }));
                expect($scope.refresh).not.toHaveBeenCalled();
                expect($scope.appserverLogs.log_entries.push).toHaveBeenCalledWith(logEntry);
                expect($scope.appserverLogs.log_error_entries.push).toHaveBeenCalledWith(logEntry);
            });
            it("do not update the AppServer's log entries for other AppServer logs", function() {
                $scope.webSocketMessageHandler(getBroadcastMessage({
                    type: "object_log_line",
                    appserver_id: 404,
                    log_entry: {created: new Date().toISOString(), level: "INFO", text: "Irrelevant log line"},
                }));
                expect($scope.refresh).not.toHaveBeenCalled();
                expect($scope.appserverLogs.log_entries.push).not.toHaveBeenCalled();
                expect($scope.appserverLogs.log_error_entries.push).not.toHaveBeenCalled();
            });
            it("update the AppServer's log entries for new VM error logs", function() {
                const logEntry = {created: new Date().toISOString(), level: "ERROR", text: "Something went wrong on the server"};
                $scope.webSocketMessageHandler(getBroadcastMessage({
                    type: "object_log_line",
                    server_id: appServerDetail.server.id,
                    log_entry: logEntry,
                }));
                expect($scope.refresh).not.toHaveBeenCalled();
                expect($scope.appserverLogs.log_entries.push).toHaveBeenCalledWith(logEntry);
                expect($scope.appserverLogs.log_error_entries.push).toHaveBeenCalledWith(logEntry);
            });
            it("do not update the AppServer's log entries for other VM logs", function() {
                $scope.webSocketMessageHandler(getBroadcastMessage({
                    type: "object_log_line",
                    server_id: 404,
                    log_entry: {created: new Date().toISOString(), level: "INFO", text: "Irrelevant log line"},
                }));
                expect($scope.refresh).not.toHaveBeenCalled();
                expect($scope.appserverLogs.log_entries.push).not.toHaveBeenCalled();
                expect($scope.appserverLogs.log_error_entries.push).not.toHaveBeenCalled();
            });
            it('do not update the AppServer or log entries details for other changes', function() {
                $scope.webSocketMessageHandler(getBroadcastMessage({type: "other_update"}));
                expect($scope.refresh).not.toHaveBeenCalled();
                expect($scope.appserverLogs.log_entries.push).not.toHaveBeenCalled();
                expect($scope.appserverLogs.log_error_entries.push).not.toHaveBeenCalled();
            });
        });
    });
});

})();
