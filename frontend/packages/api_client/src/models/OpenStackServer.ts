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

import { exists, mapValues } from '../runtime';
/**
 * 
 * @export
 * @interface OpenStackServer
 */
export interface OpenStackServer {
    /**
     * 
     * @type {number}
     * @memberof OpenStackServer
     */
    readonly id?: number;
    /**
     * 
     * @type {string}
     * @memberof OpenStackServer
     */
    readonly apiUrl?: string;
    /**
     * 
     * @type {Date}
     * @memberof OpenStackServer
     */
    readonly created?: Date;
    /**
     * 
     * @type {Date}
     * @memberof OpenStackServer
     */
    readonly modified?: Date;
    /**
     * 
     * @type {string}
     * @memberof OpenStackServer
     */
    readonly name?: string;
    /**
     * 
     * @type {string}
     * @memberof OpenStackServer
     */
    openstackId?: string;
    /**
     * 
     * @type {string}
     * @memberof OpenStackServer
     */
    readonly status?: string;
    /**
     * 
     * @type {string}
     * @memberof OpenStackServer
     */
    readonly publicIp?: string;
    /**
     * 
     * @type {string}
     * @memberof OpenStackServer
     */
    openstackRegion?: string;
}

export function OpenStackServerFromJSON(json: any): OpenStackServer {
    return OpenStackServerFromJSONTyped(json, false);
}

export function OpenStackServerFromJSONTyped(json: any, ignoreDiscriminator: boolean): OpenStackServer {
    if ((json === undefined) || (json === null)) {
        return json;
    }
    return {
        
        'id': !exists(json, 'id') ? undefined : json['id'],
        'apiUrl': !exists(json, 'api_url') ? undefined : json['api_url'],
        'created': !exists(json, 'created') ? undefined : (new Date(json['created'])),
        'modified': !exists(json, 'modified') ? undefined : (new Date(json['modified'])),
        'name': !exists(json, 'name') ? undefined : json['name'],
        'openstackId': !exists(json, 'openstack_id') ? undefined : json['openstack_id'],
        'status': !exists(json, 'status') ? undefined : json['status'],
        'publicIp': !exists(json, 'public_ip') ? undefined : json['public_ip'],
        'openstackRegion': !exists(json, 'openstack_region') ? undefined : json['openstack_region'],
    };
}

export function OpenStackServerToJSON(value?: OpenStackServer | null): any {
    if (value === undefined) {
        return undefined;
    }
    if (value === null) {
        return null;
    }
    return {
        
        'openstack_id': value.openstackId,
        'openstack_region': value.openstackRegion,
    };
}


