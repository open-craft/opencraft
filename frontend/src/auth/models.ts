/** Login model definitions */

export interface LoginStatusModel {
    error: null | string;
    /** The full name of the user */
    name: string;
    /** The OAuth2 token used to call the OCIM API */
    token: string;
    /** The username of the logged in user */
    username: string;
}
