// import { push } from 'connected-react-router';
import { OcimThunkAction } from 'global/types';
import { Action } from 'redux';
// import { Types as UIActionTypes } from 'ui/actions';
import { V2Api } from 'global/api';
// import { toCamelCase } from 'utils/string_utils';
import { LoginFormModel, LoginStateModel } from './models';

export enum Types {
  LOGIN_SUBMIT = 'LOGIN_SUBMIT',
  LOGIN_SUCCESS = 'LOGIN_SUCCESS',
  LOGIN_FAILURE = 'LOGIN_FAILURE',
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

export interface Logout extends Action {
  readonly type: Types.LOGOUT;
}

export type ActionTypes =
  | SubmitLogin
  | LoginSuccess
  | LoginFailure
  | Logout;


export const performLogin = (
  data: LoginFormModel
): OcimThunkAction<void> => async dispatch => {
    console.log(data)
    V2Api.authTokenCreate({
      data: { ...data }
    }).then((response) => {
      // Perform authentication and create new instance
      dispatch({ type: Types.LOGIN_SUCCESS, data: {...response} });
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
  dispatch({
    type: Types.LOGOUT
  });
};
