import { push } from 'connected-react-router';
import { OcimThunkAction } from 'global/types';
import { Action } from 'redux';
import { ROUTES } from 'global/constants';
// import { Types as UIActionTypes } from 'ui/actions';
import { V2Api } from 'global/api';
import { Token } from 'ocim-client';
// import { toCamelCase } from 'utils/string_utils';
import { LoginFormModel, LoginStateModel } from './models';

export enum Types {
  LOGIN_SUBMIT = 'LOGIN_SUBMIT',
  LOGIN_SUCCESS = 'LOGIN_SUCCESS',
  LOGIN_FAILURE = 'LOGIN_FAILURE',
  TOKEN_REFRESH = 'TOKEN_REFRESH',
  TOKEN_REFRESH_SUCCESS = 'TOKEN_REFRESH_SUCCESS',
  LOGOUT = 'LOGOUT'
}

export interface SubmitLogin extends Action {
  readonly type: Types.LOGIN_SUBMIT;
}

export interface LoginSuccess extends Action {
  readonly type: Types.LOGIN_SUCCESS;
  readonly data: LoginStateModel;
}

export interface LoginFailure extends Action {
  readonly type: Types.LOGIN_FAILURE;
  readonly error: any;
}

export interface TokenRefresh extends Action {
  readonly type: Types.TOKEN_REFRESH;
  readonly refreshToken: string;
}

export interface TokenRefreshSuccess extends Action {
  readonly type: Types.TOKEN_REFRESH_SUCCESS;
  readonly data: LoginStateModel;
}

export interface Logout extends Action {
  readonly type: Types.LOGOUT;
}

export type ActionTypes =
  | SubmitLogin
  | LoginSuccess
  | LoginFailure
  | TokenRefresh
  | TokenRefreshSuccess
  | Logout;

export const performLogin = (
  data: LoginFormModel,
  redirectTo?: string
): OcimThunkAction<void> => async dispatch => {
  await V2Api.authTokenCreate({ data })
    .then((response: Token) => {
      // Perform authentication and create new instance
      dispatch({ type: Types.LOGIN_SUCCESS, data: response });
      // Save auth data to localStorage so the API client picks it up
      window.localStorage.setItem('token_access', response.access);
      window.localStorage.setItem('token_refresh', response.refresh);

      if (redirectTo) {
        dispatch(push(redirectTo));
      }
    })
    .catch((e: any) => {
      e.json().then((feedback: any) => {
        // If validation fails, return error to form through state
        const error = feedback.detail;
        dispatch({
          type: Types.LOGIN_FAILURE,
          error
        });
      });
    });
};

export const performLogout = () => async (dispatch: any) => {
  window.localStorage.removeItem('token_access');
  window.localStorage.removeItem('token_refresh');
  dispatch({ type: Types.LOGOUT });
  dispatch(push(ROUTES.Auth.LOGIN));
};

export const refreshAccessToken = (
  refreshToken: string
): OcimThunkAction<void> => async dispatch => {
  await V2Api.authRefreshCreate({ data: { refresh: refreshToken } })
    .then((response: Token) => {
      // Perform authentication and create new instance
      dispatch({ type: Types.TOKEN_REFRESH_SUCCESS, data: response });
      // Save auth data to localStorage so the API client picks it up
      window.localStorage.setItem('token_access', response.access);
      window.localStorage.setItem('token_refresh', response.refresh);
    })
    .catch((e: any) => {
      window.localStorage.removeItem('token_access');
      window.localStorage.removeItem('token_refresh');

      dispatch(push(ROUTES.Auth.LOGIN));
      dispatch({ type: Types.LOGOUT });
    });
};
