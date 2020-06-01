import { push } from 'connected-react-router';
import { OcimThunkAction } from 'global/types';
import { Action } from 'redux';
import { ROUTES } from 'global/constants';
import { V2Api } from 'global/api';
import { JwtToken, Token, Email, PasswordToken } from 'ocim-client';
import { LoginFormModel, LoginStateModel } from './models';
import { clearConsoleData } from '../console/actions';
import { sanitizeErrorFeedback } from '../utils/string_utils';

export enum Types {
  EMAIL_ACTIVATION_SUBMIT = 'EMAIL_ACTIVATION_SUBMIT',
  EMAIL_ACTIVATION_SUBMIT_SUCCESS = 'EMAIL_ACTIVATION_SUBMIT_SUCCESS',
  EMAIL_ACTIVATION_SUBMIT_FAILURE = 'EMAIL_ACTIVATION_SUBMIT_FAILURE',
  LOGIN_SUBMIT = 'LOGIN_SUBMIT',
  LOGIN_SUCCESS = 'LOGIN_SUCCESS',
  LOGIN_FAILURE = 'LOGIN_FAILURE',
  TOKEN_REFRESH = 'TOKEN_REFRESH',
  TOKEN_REFRESH_SUCCESS = 'TOKEN_REFRESH_SUCCESS',
  LOGOUT = 'LOGOUT',
  PASSWORD_FORGOTTEN_SUCCESS = 'PASSWORD_FORGOTTEN_SUCCESS',
  PASSWORD_FORGOTTEN_FAILURE = 'PASSWORD_FORGOTTEN_FAILURE',
  PASSWORD_RESET_TOKEN_VALIDATION_SUCCESS = 'PASSWORD_RESET_TOKEN_VALIDATION_SUCCESS',
  PASSWORD_RESET_TOKEN_VALIDATION_FAILURE = 'PASSWORD_RESET_TOKEN_VALIDATION_FAILURE',
  PASSWORD_RESET_SUCCESS = 'PASSWORD_RESET_SUCCESS',
  PASSWORD_RESET_FAILURE = 'PASSWORD_RESET_FAILURE',
  CLEAR_ERROR_MESSAGE = 'CLEAR_ERROR_MESSAGE',
  CLEAR_SUCCESS_MESSAGE = 'CLEAR_SUCCESS_MESSAGE'
}

export interface EmailActivationSubmit extends Action {
  readonly type: Types.EMAIL_ACTIVATION_SUBMIT;
}

export interface EmailActivationSubmitSuccess extends Action {
  readonly type: Types.EMAIL_ACTIVATION_SUBMIT_SUCCESS;
}

export interface EmailActivationSubmitFailure extends Action {
  readonly type: Types.EMAIL_ACTIVATION_SUBMIT_FAILURE;
  readonly error: string | null;
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

export interface PasswordForgottenSuccess extends Action {
  readonly type: Types.PASSWORD_FORGOTTEN_SUCCESS;
  readonly succeeded: boolean;
  readonly error: null;
}
export interface PasswordForgottenFailure extends Action {
  readonly type: Types.PASSWORD_FORGOTTEN_FAILURE;
  readonly succeeded: boolean;
  readonly error: string;
}

export interface PasswordResetTokenValidationSuccess extends Action {
  readonly type: Types.PASSWORD_RESET_TOKEN_VALIDATION_SUCCESS;
  readonly succeeded: boolean;
}
export interface PasswordResetTokenValidationFailure extends Action {
  readonly type: Types.PASSWORD_RESET_TOKEN_VALIDATION_FAILURE;
  readonly succeeded: boolean;
  readonly error: string;
}

export interface PasswordResetSuccess extends Action {
  readonly type: Types.PASSWORD_RESET_SUCCESS;
}
export interface PasswordResetFailure extends Action {
  readonly type: Types.PASSWORD_RESET_FAILURE;
  readonly error: string;
}

export interface ClearErrorMessage extends Action {
  readonly type: Types.CLEAR_ERROR_MESSAGE;
  readonly error: null;
}

export interface ClearSuccessMessage extends Action {
  readonly type: Types.CLEAR_SUCCESS_MESSAGE;
  readonly succeeded: boolean;
}

export type ActionTypes =
  | EmailActivationSubmit
  | EmailActivationSubmitSuccess
  | EmailActivationSubmitFailure
  | SubmitLogin
  | LoginSuccess
  | LoginFailure
  | TokenRefresh
  | TokenRefreshSuccess
  | Logout
  | PasswordForgottenSuccess
  | PasswordForgottenFailure
  | PasswordResetTokenValidationSuccess
  | PasswordResetTokenValidationFailure
  | PasswordResetSuccess
  | PasswordResetFailure
  | ClearErrorMessage
  | ClearSuccessMessage;

export const clearErrorMessage = () => async (dispatch: any) => {
  dispatch({ type: Types.CLEAR_ERROR_MESSAGE });
};

export const clearSuccessMessage = () => async (dispatch: any) => {
  dispatch({ type: Types.CLEAR_SUCCESS_MESSAGE });
};

/**
 * Perform email activation request.
 *
 * Uses the V2Api and submits the email confirmation code to the backend.
 * If the request fails, just show a generic error message.
 */
export const performEmailActivation = (
  verificationCode: string
): OcimThunkAction<void> => async dispatch => {
  dispatch({ type: Types.EMAIL_ACTIVATION_SUBMIT });

  try {
    // We don't need the response, if the request goes through
    // then the email activation succeeded.
    await V2Api.verifyEmailRead({ id: verificationCode });
    dispatch({ type: Types.EMAIL_ACTIVATION_SUBMIT_SUCCESS });
  } catch (e) {
    // If any error happends, push user to the error page.
    dispatch({ type: Types.EMAIL_ACTIVATION_SUBMIT_FAILURE });
  }
};

export const performLogin = (
  data: LoginFormModel,
  redirectTo?: string
): OcimThunkAction<void> => async dispatch => {
  await V2Api.authTokenCreate({ data })
    .then((response: JwtToken) => {
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
      try {
        e.json().then((feedback: any) => {
          // If validation fails, return error to form through state
          let error = feedback.detail;
          // Don't provide individual feedback on each field for login
          // If feedback.detail isn't set, then it means we got an
          // response like this:
          // {
          //    username: ["This field is required.]
          // }
          // So manually set feedback error message.
          if (!feedback.detail) {
            error = 'Both the username and password fields are required.';
          }
          dispatch({ type: Types.CLEAR_SUCCESS_MESSAGE });
          dispatch({
            type: Types.LOGIN_FAILURE,
            error
          });
        });
      } catch (jsonParseError) {
        dispatch(push(ROUTES.Error.UNKNOWN_ERROR));
      }
    });
};

export const performLogout = () => async (dispatch: any) => {
  window.localStorage.removeItem('token_access');
  window.localStorage.removeItem('token_refresh');
  dispatch({ type: Types.LOGOUT });
  dispatch(clearConsoleData());
  dispatch(push(ROUTES.Auth.LOGIN));
};

export const refreshAccessToken = (
  refreshToken: string
): OcimThunkAction<void> => async dispatch => {
  await V2Api.authRefreshCreate({ data: { refresh: refreshToken } })
    .then((response: JwtToken) => {
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

export const performPasswordForgotten = (
  data: Email
): OcimThunkAction<void> => async dispatch => {
  await V2Api.passwordResetCreate({ data })
    .then(() => {
      dispatch({ type: Types.PASSWORD_FORGOTTEN_SUCCESS });
    })
    .catch((e: any) => {
      try {
        e.json().then((feedback: any) => {
          // If validation fails, return error to form through state
          const error = sanitizeErrorFeedback(feedback).email;
          dispatch({
            type: Types.PASSWORD_FORGOTTEN_FAILURE,
            error
          });
        });
      } catch (jsonParseError) {
        dispatch(push(ROUTES.Error.UNKNOWN_ERROR));
      }
    });
};

export const performPasswordResetTokenValidation = (
  data: Token
): OcimThunkAction<void> => async dispatch => {
  await V2Api.passwordResetValidateTokenCreate({ data })
    .then(() => {
      dispatch({ type: Types.PASSWORD_RESET_TOKEN_VALIDATION_SUCCESS });
    })
    .catch(() => {
      const error = 'Invalid token';
      dispatch({ type: Types.PASSWORD_RESET_TOKEN_VALIDATION_FAILURE, error });
    });
};

export const performPasswordReset = (
  data: PasswordToken
): OcimThunkAction<void> => async dispatch => {
  await V2Api.passwordResetConfirmCreate({ data })
    .then(() => {
      dispatch({ type: Types.PASSWORD_RESET_SUCCESS });
      dispatch(push(ROUTES.Auth.LOGIN));
    })
    .catch((e: any) => {
      try {
        e.json().then((feedback: any) => {
          // If validation fails, return error to form through state
          const error = sanitizeErrorFeedback(feedback).password;
          dispatch({
            type: Types.PASSWORD_RESET_FAILURE,
            error
          });
        });
      } catch (jsonParseError) {
        dispatch(push(ROUTES.Error.UNKNOWN_ERROR));
      }
    });
};
