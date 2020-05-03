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
 * @interface PasswordToken
 */
export interface PasswordToken {
    /**
     * 
     * @type {string}
     * @memberof PasswordToken
     */
    password: string;
    /**
     * 
     * @type {string}
     * @memberof PasswordToken
     */
    token: string;
}

export function PasswordTokenFromJSON(json: any): PasswordToken {
    return PasswordTokenFromJSONTyped(json, false);
}

export function PasswordTokenFromJSONTyped(json: any, ignoreDiscriminator: boolean): PasswordToken {
    if ((json === undefined) || (json === null)) {
        return json;
    }
    return {
        
        'password': json['password'],
        'token': json['token'],
    };
}

export function PasswordTokenToJSON(value?: PasswordToken | null): any {
    if (value === undefined) {
        return undefined;
    }
    if (value === null) {
        return null;
    }
    return {
        
        'password': value.password,
        'token': value.token,
    };
}


