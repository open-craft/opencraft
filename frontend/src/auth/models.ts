/** Login model definitions */

export interface LoginFormModel {
  /** The full name of the user */
  username: string;
  /** The password of the user */
  password: string;
}

export interface LoginStateModel extends LoginFormModel {
  error: null | string;
  /** The JWT token used to call Ocim API */
  access: string;
  /** The JWT refresh token to renew auth token */
  refresh: string;
  /** State of login request */
  loading: boolean;
}

export const notLoggedInStatus: LoginStateModel = {
  error: null,
  username: '',
  password: '',
  access: '',
  refresh: '',
  loading: false
};
