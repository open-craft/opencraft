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
 * @interface OpenEdXInstanceDeploymentStatus
 */
export interface OpenEdXInstanceDeploymentStatus {
    /**
     * 
     * @type {string}
     * @memberof OpenEdXInstanceDeploymentStatus
     */
    status: OpenEdXInstanceDeploymentStatusStatusEnum;
    /**
     * 
     * @type {object}
     * @memberof OpenEdXInstanceDeploymentStatus
     */
    undeployedChanges: object;
    /**
     * 
     * @type {object}
     * @memberof OpenEdXInstanceDeploymentStatus
     */
    deployedChanges: object;
    /**
     * 
     * @type {string}
     * @memberof OpenEdXInstanceDeploymentStatus
     */
    deploymentType: OpenEdXInstanceDeploymentStatusDeploymentTypeEnum;
}

/**
* @export
* @enum {string}
*/
export enum OpenEdXInstanceDeploymentStatusStatusEnum {
    Healthy = 'healthy',
    Unhealthy = 'unhealthy',
    Offline = 'offline',
    Provisioning = 'provisioning',
    Preparing = 'preparing',
    ChangesPending = 'changes_pending'
}/**
* @export
* @enum {string}
*/
export enum OpenEdXInstanceDeploymentStatusDeploymentTypeEnum {
    User = 'user',
    Batch = 'batch',
    Admin = 'admin',
    Pr = 'pr',
    Periodic = 'periodic',
    Registration = 'registration',
    Unknown = 'unknown'
}

export function OpenEdXInstanceDeploymentStatusFromJSON(json: any): OpenEdXInstanceDeploymentStatus {
    return OpenEdXInstanceDeploymentStatusFromJSONTyped(json, false);
}

export function OpenEdXInstanceDeploymentStatusFromJSONTyped(json: any, ignoreDiscriminator: boolean): OpenEdXInstanceDeploymentStatus {
    if ((json === undefined) || (json === null)) {
        return json;
    }
    return {
        
        'status': json['status'],
        'undeployedChanges': json['undeployed_changes'],
        'deployedChanges': json['deployed_changes'],
        'deploymentType': json['deployment_type'],
    };
}

export function OpenEdXInstanceDeploymentStatusToJSON(value?: OpenEdXInstanceDeploymentStatus | null): any {
    if (value === undefined) {
        return undefined;
    }
    if (value === null) {
        return null;
    }
    return {
        
        'status': value.status,
        'undeployed_changes': value.undeployedChanges,
        'deployed_changes': value.deployedChanges,
        'deployment_type': value.deploymentType,
    };
}


