/* tslint:disable */
/* eslint-disable */
/**
 * OpenCraft Instance Manager
 * API for OpenCraft Instance Manager
 *
 * The version of the OpenAPI document: api
 * 
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */


import * as runtime from '../runtime';
import {
    InstanceReferenceDetailed,
    InstanceReferenceDetailedFromJSON,
    InstanceReferenceDetailedToJSON,
    OpenEdXAppServer,
    OpenEdXAppServerFromJSON,
    OpenEdXAppServerToJSON,
    OpenStackServer,
    OpenStackServerFromJSON,
    OpenStackServerToJSON,
    SpawnAppServer,
    SpawnAppServerFromJSON,
    SpawnAppServerToJSON,
    WatchedPullRequest,
    WatchedPullRequestFromJSON,
    WatchedPullRequestToJSON,
} from '../models';

export interface InstanceAppServersRequest {
    id: number;
}

export interface InstanceLogsRequest {
    id: number;
}

export interface InstanceReadRequest {
    id: number;
}

export interface OpenedxAppserverCreateRequest {
    data: SpawnAppServer;
}

export interface OpenedxAppserverLogsRequest {
    id: number;
}

export interface OpenedxAppserverMakeActiveRequest {
    id: number;
    data: OpenEdXAppServer;
}

export interface OpenedxAppserverMakeInactiveRequest {
    id: number;
    data: OpenEdXAppServer;
}

export interface OpenedxAppserverReadRequest {
    id: number;
}

export interface OpenedxAppserverTerminateRequest {
    id: number;
    data: OpenEdXAppServer;
}

export interface OpenstackserverReadRequest {
    id: number;
}

export interface PrWatchReadRequest {
    id: number;
}

export interface PrWatchUpdateInstanceRequest {
    id: number;
    data: object;
}

/**
 * no description
 */
export class V1Api extends runtime.BaseAPI {

    /**
     * Get this Instance\'s entire list of AppServers
     */
    async instanceAppServersRaw(requestParameters: InstanceAppServersRequest): Promise<runtime.ApiResponse<InstanceReferenceDetailed>> {
        if (requestParameters.id === null || requestParameters.id === undefined) {
            throw new runtime.RequiredError('id','Required parameter requestParameters.id was null or undefined when calling instanceAppServers.');
        }

        const queryParameters: runtime.HTTPQuery = {};

        const headerParameters: runtime.HTTPHeaders = {};

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = this.configuration.apiKey("Authorization"); // api_key authentication
        }

        if (this.configuration && (this.configuration.username !== undefined || this.configuration.password !== undefined)) {
            headerParameters["Authorization"] = "Basic " + btoa(this.configuration.username + ":" + this.configuration.password);
        }
        const response = await this.request({
            path: `/v1/instance/{id}/app_servers/`.replace(`{${"id"}}`, encodeURIComponent(String(requestParameters.id))),
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        });

        return new runtime.JSONApiResponse(response, (jsonValue) => InstanceReferenceDetailedFromJSON(jsonValue));
    }

    /**
     * Get this Instance\'s entire list of AppServers
     */
    async instanceAppServers(requestParameters: InstanceAppServersRequest): Promise<InstanceReferenceDetailed> {
        const response = await this.instanceAppServersRaw(requestParameters);
        return await response.value();
    }

    /**
     * List all instances. No App server list is returned in the list view, only the newest app server information.
     */
    async instanceListRaw(): Promise<runtime.ApiResponse<Array<InstanceReferenceDetailed>>> {
        const queryParameters: runtime.HTTPQuery = {};

        const headerParameters: runtime.HTTPHeaders = {};

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = this.configuration.apiKey("Authorization"); // api_key authentication
        }

        if (this.configuration && (this.configuration.username !== undefined || this.configuration.password !== undefined)) {
            headerParameters["Authorization"] = "Basic " + btoa(this.configuration.username + ":" + this.configuration.password);
        }
        const response = await this.request({
            path: `/v1/instance/`,
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        });

        return new runtime.JSONApiResponse(response, (jsonValue) => jsonValue.map(InstanceReferenceDetailedFromJSON));
    }

    /**
     * List all instances. No App server list is returned in the list view, only the newest app server information.
     */
    async instanceList(): Promise<Array<InstanceReferenceDetailed>> {
        const response = await this.instanceListRaw();
        return await response.value();
    }

    /**
     * Get this Instance\'s log entries
     */
    async instanceLogsRaw(requestParameters: InstanceLogsRequest): Promise<runtime.ApiResponse<InstanceReferenceDetailed>> {
        if (requestParameters.id === null || requestParameters.id === undefined) {
            throw new runtime.RequiredError('id','Required parameter requestParameters.id was null or undefined when calling instanceLogs.');
        }

        const queryParameters: runtime.HTTPQuery = {};

        const headerParameters: runtime.HTTPHeaders = {};

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = this.configuration.apiKey("Authorization"); // api_key authentication
        }

        if (this.configuration && (this.configuration.username !== undefined || this.configuration.password !== undefined)) {
            headerParameters["Authorization"] = "Basic " + btoa(this.configuration.username + ":" + this.configuration.password);
        }
        const response = await this.request({
            path: `/v1/instance/{id}/logs/`.replace(`{${"id"}}`, encodeURIComponent(String(requestParameters.id))),
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        });

        return new runtime.JSONApiResponse(response, (jsonValue) => InstanceReferenceDetailedFromJSON(jsonValue));
    }

    /**
     * Get this Instance\'s log entries
     */
    async instanceLogs(requestParameters: InstanceLogsRequest): Promise<InstanceReferenceDetailed> {
        const response = await this.instanceLogsRaw(requestParameters);
        return await response.value();
    }

    /**
     * Uses InstanceReference to iterate all types of instances, and serializes them.  The fields that are returned for each instance depend on its instance_type and whether you are listing all instances (returns fewer fields) or just one instance (returns all fields).  The only fields that are available for all instances, regardless of type, are the fields defined on the InstanceReference class, namely:  * `id` * `name` * `created` * `modified` * `instance_type` * `is_archived`  Note that IDs used for instances are always the ID of the InstanceReference object, which may not be the same as the ID of the specific Instance subclass (e.g. the OpenEdXInstance object has its own ID which should never be used - just use its InstanceReference ID). This detail is managed by the API so users of the API should not generally need to be aware of it.
     * API to list and manipulate instances.
     */
    async instanceReadRaw(requestParameters: InstanceReadRequest): Promise<runtime.ApiResponse<InstanceReferenceDetailed>> {
        if (requestParameters.id === null || requestParameters.id === undefined) {
            throw new runtime.RequiredError('id','Required parameter requestParameters.id was null or undefined when calling instanceRead.');
        }

        const queryParameters: runtime.HTTPQuery = {};

        const headerParameters: runtime.HTTPHeaders = {};

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = this.configuration.apiKey("Authorization"); // api_key authentication
        }

        if (this.configuration && (this.configuration.username !== undefined || this.configuration.password !== undefined)) {
            headerParameters["Authorization"] = "Basic " + btoa(this.configuration.username + ":" + this.configuration.password);
        }
        const response = await this.request({
            path: `/v1/instance/{id}/`.replace(`{${"id"}}`, encodeURIComponent(String(requestParameters.id))),
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        });

        return new runtime.JSONApiResponse(response, (jsonValue) => InstanceReferenceDetailedFromJSON(jsonValue));
    }

    /**
     * Uses InstanceReference to iterate all types of instances, and serializes them.  The fields that are returned for each instance depend on its instance_type and whether you are listing all instances (returns fewer fields) or just one instance (returns all fields).  The only fields that are available for all instances, regardless of type, are the fields defined on the InstanceReference class, namely:  * `id` * `name` * `created` * `modified` * `instance_type` * `is_archived`  Note that IDs used for instances are always the ID of the InstanceReference object, which may not be the same as the ID of the specific Instance subclass (e.g. the OpenEdXInstance object has its own ID which should never be used - just use its InstanceReference ID). This detail is managed by the API so users of the API should not generally need to be aware of it.
     * API to list and manipulate instances.
     */
    async instanceRead(requestParameters: InstanceReadRequest): Promise<InstanceReferenceDetailed> {
        const response = await this.instanceReadRaw(requestParameters);
        return await response.value();
    }

    /**
     * Must pass a parameter called \'instance_id\' which is the ID of the InstanceReference of the OpenEdXInstance that this AppServer is for.
     * Spawn a new AppServer for an existing OpenEdXInstance
     */
    async openedxAppserverCreateRaw(requestParameters: OpenedxAppserverCreateRequest): Promise<runtime.ApiResponse<SpawnAppServer>> {
        if (requestParameters.data === null || requestParameters.data === undefined) {
            throw new runtime.RequiredError('data','Required parameter requestParameters.data was null or undefined when calling openedxAppserverCreate.');
        }

        const queryParameters: runtime.HTTPQuery = {};

        const headerParameters: runtime.HTTPHeaders = {};

        headerParameters['Content-Type'] = 'application/json';

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = this.configuration.apiKey("Authorization"); // api_key authentication
        }

        if (this.configuration && (this.configuration.username !== undefined || this.configuration.password !== undefined)) {
            headerParameters["Authorization"] = "Basic " + btoa(this.configuration.username + ":" + this.configuration.password);
        }
        const response = await this.request({
            path: `/v1/openedx_appserver/`,
            method: 'POST',
            headers: headerParameters,
            query: queryParameters,
            body: SpawnAppServerToJSON(requestParameters.data),
        });

        return new runtime.JSONApiResponse(response, (jsonValue) => SpawnAppServerFromJSON(jsonValue));
    }

    /**
     * Must pass a parameter called \'instance_id\' which is the ID of the InstanceReference of the OpenEdXInstance that this AppServer is for.
     * Spawn a new AppServer for an existing OpenEdXInstance
     */
    async openedxAppserverCreate(requestParameters: OpenedxAppserverCreateRequest): Promise<SpawnAppServer> {
        const response = await this.openedxAppserverCreateRaw(requestParameters);
        return await response.value();
    }

    /**
     * API to list and manipulate Open edX AppServers.
     */
    async openedxAppserverListRaw(): Promise<runtime.ApiResponse<Array<string>>> {
        const queryParameters: runtime.HTTPQuery = {};

        const headerParameters: runtime.HTTPHeaders = {};

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = this.configuration.apiKey("Authorization"); // api_key authentication
        }

        if (this.configuration && (this.configuration.username !== undefined || this.configuration.password !== undefined)) {
            headerParameters["Authorization"] = "Basic " + btoa(this.configuration.username + ":" + this.configuration.password);
        }
        const response = await this.request({
            path: `/v1/openedx_appserver/`,
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        });

        return new runtime.JSONApiResponse<any>(response);
    }

    /**
     * API to list and manipulate Open edX AppServers.
     */
    async openedxAppserverList(): Promise<Array<string>> {
        const response = await this.openedxAppserverListRaw();
        return await response.value();
    }

    /**
     * Get this AppServer\'s log entries
     */
    async openedxAppserverLogsRaw(requestParameters: OpenedxAppserverLogsRequest): Promise<runtime.ApiResponse<OpenEdXAppServer>> {
        if (requestParameters.id === null || requestParameters.id === undefined) {
            throw new runtime.RequiredError('id','Required parameter requestParameters.id was null or undefined when calling openedxAppserverLogs.');
        }

        const queryParameters: runtime.HTTPQuery = {};

        const headerParameters: runtime.HTTPHeaders = {};

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = this.configuration.apiKey("Authorization"); // api_key authentication
        }

        if (this.configuration && (this.configuration.username !== undefined || this.configuration.password !== undefined)) {
            headerParameters["Authorization"] = "Basic " + btoa(this.configuration.username + ":" + this.configuration.password);
        }
        const response = await this.request({
            path: `/v1/openedx_appserver/{id}/logs/`.replace(`{${"id"}}`, encodeURIComponent(String(requestParameters.id))),
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        });

        return new runtime.JSONApiResponse(response, (jsonValue) => OpenEdXAppServerFromJSON(jsonValue));
    }

    /**
     * Get this AppServer\'s log entries
     */
    async openedxAppserverLogs(requestParameters: OpenedxAppserverLogsRequest): Promise<OpenEdXAppServer> {
        const response = await this.openedxAppserverLogsRaw(requestParameters);
        return await response.value();
    }

    /**
     * Add this AppServer to the list of active app server for the instance.
     */
    async openedxAppserverMakeActiveRaw(requestParameters: OpenedxAppserverMakeActiveRequest): Promise<runtime.ApiResponse<OpenEdXAppServer>> {
        if (requestParameters.id === null || requestParameters.id === undefined) {
            throw new runtime.RequiredError('id','Required parameter requestParameters.id was null or undefined when calling openedxAppserverMakeActive.');
        }

        if (requestParameters.data === null || requestParameters.data === undefined) {
            throw new runtime.RequiredError('data','Required parameter requestParameters.data was null or undefined when calling openedxAppserverMakeActive.');
        }

        const queryParameters: runtime.HTTPQuery = {};

        const headerParameters: runtime.HTTPHeaders = {};

        headerParameters['Content-Type'] = 'application/json';

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = this.configuration.apiKey("Authorization"); // api_key authentication
        }

        if (this.configuration && (this.configuration.username !== undefined || this.configuration.password !== undefined)) {
            headerParameters["Authorization"] = "Basic " + btoa(this.configuration.username + ":" + this.configuration.password);
        }
        const response = await this.request({
            path: `/v1/openedx_appserver/{id}/make_active/`.replace(`{${"id"}}`, encodeURIComponent(String(requestParameters.id))),
            method: 'POST',
            headers: headerParameters,
            query: queryParameters,
            body: OpenEdXAppServerToJSON(requestParameters.data),
        });

        return new runtime.JSONApiResponse(response, (jsonValue) => OpenEdXAppServerFromJSON(jsonValue));
    }

    /**
     * Add this AppServer to the list of active app server for the instance.
     */
    async openedxAppserverMakeActive(requestParameters: OpenedxAppserverMakeActiveRequest): Promise<OpenEdXAppServer> {
        const response = await this.openedxAppserverMakeActiveRaw(requestParameters);
        return await response.value();
    }

    /**
     * Remove this AppServer from the list of active app server for the instance.
     */
    async openedxAppserverMakeInactiveRaw(requestParameters: OpenedxAppserverMakeInactiveRequest): Promise<runtime.ApiResponse<OpenEdXAppServer>> {
        if (requestParameters.id === null || requestParameters.id === undefined) {
            throw new runtime.RequiredError('id','Required parameter requestParameters.id was null or undefined when calling openedxAppserverMakeInactive.');
        }

        if (requestParameters.data === null || requestParameters.data === undefined) {
            throw new runtime.RequiredError('data','Required parameter requestParameters.data was null or undefined when calling openedxAppserverMakeInactive.');
        }

        const queryParameters: runtime.HTTPQuery = {};

        const headerParameters: runtime.HTTPHeaders = {};

        headerParameters['Content-Type'] = 'application/json';

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = this.configuration.apiKey("Authorization"); // api_key authentication
        }

        if (this.configuration && (this.configuration.username !== undefined || this.configuration.password !== undefined)) {
            headerParameters["Authorization"] = "Basic " + btoa(this.configuration.username + ":" + this.configuration.password);
        }
        const response = await this.request({
            path: `/v1/openedx_appserver/{id}/make_inactive/`.replace(`{${"id"}}`, encodeURIComponent(String(requestParameters.id))),
            method: 'POST',
            headers: headerParameters,
            query: queryParameters,
            body: OpenEdXAppServerToJSON(requestParameters.data),
        });

        return new runtime.JSONApiResponse(response, (jsonValue) => OpenEdXAppServerFromJSON(jsonValue));
    }

    /**
     * Remove this AppServer from the list of active app server for the instance.
     */
    async openedxAppserverMakeInactive(requestParameters: OpenedxAppserverMakeInactiveRequest): Promise<OpenEdXAppServer> {
        const response = await this.openedxAppserverMakeInactiveRaw(requestParameters);
        return await response.value();
    }

    /**
     * API to list and manipulate Open edX AppServers.
     */
    async openedxAppserverReadRaw(requestParameters: OpenedxAppserverReadRequest): Promise<runtime.ApiResponse<OpenEdXAppServer>> {
        if (requestParameters.id === null || requestParameters.id === undefined) {
            throw new runtime.RequiredError('id','Required parameter requestParameters.id was null or undefined when calling openedxAppserverRead.');
        }

        const queryParameters: runtime.HTTPQuery = {};

        const headerParameters: runtime.HTTPHeaders = {};

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = this.configuration.apiKey("Authorization"); // api_key authentication
        }

        if (this.configuration && (this.configuration.username !== undefined || this.configuration.password !== undefined)) {
            headerParameters["Authorization"] = "Basic " + btoa(this.configuration.username + ":" + this.configuration.password);
        }
        const response = await this.request({
            path: `/v1/openedx_appserver/{id}/`.replace(`{${"id"}}`, encodeURIComponent(String(requestParameters.id))),
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        });

        return new runtime.JSONApiResponse(response, (jsonValue) => OpenEdXAppServerFromJSON(jsonValue));
    }

    /**
     * API to list and manipulate Open edX AppServers.
     */
    async openedxAppserverRead(requestParameters: OpenedxAppserverReadRequest): Promise<OpenEdXAppServer> {
        const response = await this.openedxAppserverReadRaw(requestParameters);
        return await response.value();
    }

    /**
     * Terminate the VM running the provided AppServer.
     */
    async openedxAppserverTerminateRaw(requestParameters: OpenedxAppserverTerminateRequest): Promise<runtime.ApiResponse<OpenEdXAppServer>> {
        if (requestParameters.id === null || requestParameters.id === undefined) {
            throw new runtime.RequiredError('id','Required parameter requestParameters.id was null or undefined when calling openedxAppserverTerminate.');
        }

        if (requestParameters.data === null || requestParameters.data === undefined) {
            throw new runtime.RequiredError('data','Required parameter requestParameters.data was null or undefined when calling openedxAppserverTerminate.');
        }

        const queryParameters: runtime.HTTPQuery = {};

        const headerParameters: runtime.HTTPHeaders = {};

        headerParameters['Content-Type'] = 'application/json';

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = this.configuration.apiKey("Authorization"); // api_key authentication
        }

        if (this.configuration && (this.configuration.username !== undefined || this.configuration.password !== undefined)) {
            headerParameters["Authorization"] = "Basic " + btoa(this.configuration.username + ":" + this.configuration.password);
        }
        const response = await this.request({
            path: `/v1/openedx_appserver/{id}/terminate/`.replace(`{${"id"}}`, encodeURIComponent(String(requestParameters.id))),
            method: 'POST',
            headers: headerParameters,
            query: queryParameters,
            body: OpenEdXAppServerToJSON(requestParameters.data),
        });

        return new runtime.JSONApiResponse(response, (jsonValue) => OpenEdXAppServerFromJSON(jsonValue));
    }

    /**
     * Terminate the VM running the provided AppServer.
     */
    async openedxAppserverTerminate(requestParameters: OpenedxAppserverTerminateRequest): Promise<OpenEdXAppServer> {
        const response = await this.openedxAppserverTerminateRaw(requestParameters);
        return await response.value();
    }

    /**
     * This API allows you retrieve information about OpenStackServer objects (OpenStack VMs). It is visible only to superusers because if we open it to instance managers we need to filter VMs by organization. Since this API isn\'t used by the UI, for now we keep it internal and superuser only.
     */
    async openstackserverListRaw(): Promise<runtime.ApiResponse<Array<OpenStackServer>>> {
        const queryParameters: runtime.HTTPQuery = {};

        const headerParameters: runtime.HTTPHeaders = {};

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = this.configuration.apiKey("Authorization"); // api_key authentication
        }

        if (this.configuration && (this.configuration.username !== undefined || this.configuration.password !== undefined)) {
            headerParameters["Authorization"] = "Basic " + btoa(this.configuration.username + ":" + this.configuration.password);
        }
        const response = await this.request({
            path: `/v1/openstackserver/`,
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        });

        return new runtime.JSONApiResponse(response, (jsonValue) => jsonValue.map(OpenStackServerFromJSON));
    }

    /**
     * This API allows you retrieve information about OpenStackServer objects (OpenStack VMs). It is visible only to superusers because if we open it to instance managers we need to filter VMs by organization. Since this API isn\'t used by the UI, for now we keep it internal and superuser only.
     */
    async openstackserverList(): Promise<Array<OpenStackServer>> {
        const response = await this.openstackserverListRaw();
        return await response.value();
    }

    /**
     * This API allows you retrieve information about OpenStackServer objects (OpenStack VMs). It is visible only to superusers because if we open it to instance managers we need to filter VMs by organization. Since this API isn\'t used by the UI, for now we keep it internal and superuser only.
     */
    async openstackserverReadRaw(requestParameters: OpenstackserverReadRequest): Promise<runtime.ApiResponse<OpenStackServer>> {
        if (requestParameters.id === null || requestParameters.id === undefined) {
            throw new runtime.RequiredError('id','Required parameter requestParameters.id was null or undefined when calling openstackserverRead.');
        }

        const queryParameters: runtime.HTTPQuery = {};

        const headerParameters: runtime.HTTPHeaders = {};

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = this.configuration.apiKey("Authorization"); // api_key authentication
        }

        if (this.configuration && (this.configuration.username !== undefined || this.configuration.password !== undefined)) {
            headerParameters["Authorization"] = "Basic " + btoa(this.configuration.username + ":" + this.configuration.password);
        }
        const response = await this.request({
            path: `/v1/openstackserver/{id}/`.replace(`{${"id"}}`, encodeURIComponent(String(requestParameters.id))),
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        });

        return new runtime.JSONApiResponse(response, (jsonValue) => OpenStackServerFromJSON(jsonValue));
    }

    /**
     * This API allows you retrieve information about OpenStackServer objects (OpenStack VMs). It is visible only to superusers because if we open it to instance managers we need to filter VMs by organization. Since this API isn\'t used by the UI, for now we keep it internal and superuser only.
     */
    async openstackserverRead(requestParameters: OpenstackserverReadRequest): Promise<OpenStackServer> {
        const response = await this.openstackserverReadRaw(requestParameters);
        return await response.value();
    }

    /**
     * API to update instances from their PR
     */
    async prWatchListRaw(): Promise<runtime.ApiResponse<Array<WatchedPullRequest>>> {
        const queryParameters: runtime.HTTPQuery = {};

        const headerParameters: runtime.HTTPHeaders = {};

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = this.configuration.apiKey("Authorization"); // api_key authentication
        }

        if (this.configuration && (this.configuration.username !== undefined || this.configuration.password !== undefined)) {
            headerParameters["Authorization"] = "Basic " + btoa(this.configuration.username + ":" + this.configuration.password);
        }
        const response = await this.request({
            path: `/v1/pr_watch/`,
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        });

        return new runtime.JSONApiResponse(response, (jsonValue) => jsonValue.map(WatchedPullRequestFromJSON));
    }

    /**
     * API to update instances from their PR
     */
    async prWatchList(): Promise<Array<WatchedPullRequest>> {
        const response = await this.prWatchListRaw();
        return await response.value();
    }

    /**
     * API to update instances from their PR
     */
    async prWatchReadRaw(requestParameters: PrWatchReadRequest): Promise<runtime.ApiResponse<WatchedPullRequest>> {
        if (requestParameters.id === null || requestParameters.id === undefined) {
            throw new runtime.RequiredError('id','Required parameter requestParameters.id was null or undefined when calling prWatchRead.');
        }

        const queryParameters: runtime.HTTPQuery = {};

        const headerParameters: runtime.HTTPHeaders = {};

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = this.configuration.apiKey("Authorization"); // api_key authentication
        }

        if (this.configuration && (this.configuration.username !== undefined || this.configuration.password !== undefined)) {
            headerParameters["Authorization"] = "Basic " + btoa(this.configuration.username + ":" + this.configuration.password);
        }
        const response = await this.request({
            path: `/v1/pr_watch/{id}/`.replace(`{${"id"}}`, encodeURIComponent(String(requestParameters.id))),
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        });

        return new runtime.JSONApiResponse(response, (jsonValue) => WatchedPullRequestFromJSON(jsonValue));
    }

    /**
     * API to update instances from their PR
     */
    async prWatchRead(requestParameters: PrWatchReadRequest): Promise<WatchedPullRequest> {
        const response = await this.prWatchReadRaw(requestParameters);
        return await response.value();
    }

    /**
     * This will update the instance\'s settings, but will not provision a new AppServer.
     * Update the instance associated with this PR, creating it if necessary.
     */
    async prWatchUpdateInstanceRaw(requestParameters: PrWatchUpdateInstanceRequest): Promise<runtime.ApiResponse<object>> {
        if (requestParameters.id === null || requestParameters.id === undefined) {
            throw new runtime.RequiredError('id','Required parameter requestParameters.id was null or undefined when calling prWatchUpdateInstance.');
        }

        if (requestParameters.data === null || requestParameters.data === undefined) {
            throw new runtime.RequiredError('data','Required parameter requestParameters.data was null or undefined when calling prWatchUpdateInstance.');
        }

        const queryParameters: runtime.HTTPQuery = {};

        const headerParameters: runtime.HTTPHeaders = {};

        headerParameters['Content-Type'] = 'application/json';

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = this.configuration.apiKey("Authorization"); // api_key authentication
        }

        if (this.configuration && (this.configuration.username !== undefined || this.configuration.password !== undefined)) {
            headerParameters["Authorization"] = "Basic " + btoa(this.configuration.username + ":" + this.configuration.password);
        }
        const response = await this.request({
            path: `/v1/pr_watch/{id}/update_instance/`.replace(`{${"id"}}`, encodeURIComponent(String(requestParameters.id))),
            method: 'POST',
            headers: headerParameters,
            query: queryParameters,
            body: requestParameters.data as any,
        });

        return new runtime.JSONApiResponse<any>(response);
    }

    /**
     * This will update the instance\'s settings, but will not provision a new AppServer.
     * Update the instance associated with this PR, creating it if necessary.
     */
    async prWatchUpdateInstance(requestParameters: PrWatchUpdateInstanceRequest): Promise<object> {
        const response = await this.prWatchUpdateInstanceRaw(requestParameters);
        return await response.value();
    }

    /**
     * Not really a list view, but we have to use `list` to fit into ViewSet semantics so this can be part of the browsable api.
     * Validate the given form input, and return any errors as json.
     */
    async registrationRegisterValidateCreateRaw(): Promise<runtime.ApiResponse<void>> {
        const queryParameters: runtime.HTTPQuery = {};

        const headerParameters: runtime.HTTPHeaders = {};

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = this.configuration.apiKey("Authorization"); // api_key authentication
        }

        if (this.configuration && (this.configuration.username !== undefined || this.configuration.password !== undefined)) {
            headerParameters["Authorization"] = "Basic " + btoa(this.configuration.username + ":" + this.configuration.password);
        }
        const response = await this.request({
            path: `/v1/registration/register/validate/`,
            method: 'POST',
            headers: headerParameters,
            query: queryParameters,
        });

        return new runtime.VoidApiResponse(response);
    }

    /**
     * Not really a list view, but we have to use `list` to fit into ViewSet semantics so this can be part of the browsable api.
     * Validate the given form input, and return any errors as json.
     */
    async registrationRegisterValidateCreate(): Promise<void> {
        await this.registrationRegisterValidateCreateRaw();
    }

}
