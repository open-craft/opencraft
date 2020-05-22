import update from 'immutability-helper';
import * as LoginActions from './actions';
import { getInitialState, notLoggedInStatus, LoginStateModel } from './models';

export const initialState: Readonly<LoginStateModel> = getInitialState();

export function loginStateReducer(
  state = initialState,
  action: LoginActions.ActionTypes
): LoginStateModel {
  switch (action.type) {
    case LoginActions.Types.EMAIL_ACTIVATION_SUBMIT:
      return update(state, { loading: { $set: true } });
    case LoginActions.Types.EMAIL_ACTIVATION_SUBMIT_SUCCESS:
      return update(state, {
        succeeded: { $set: true },
        loading: { $set: false }
      });
    case LoginActions.Types.EMAIL_ACTIVATION_SUBMIT_FAILURE:
      return update(state, {
        loading: { $set: false },
        error: { $set: action.error }
      });
    case LoginActions.Types.LOGIN_SUBMIT:
      return update(state, { loading: { $set: true } });
    case LoginActions.Types.LOGIN_SUCCESS:
      return update(state, {
        $merge: action.data,
        loading: { $set: false }
      });
    case LoginActions.Types.LOGIN_FAILURE:
      return update(state, {
        error: { $set: action.error },
        loading: { $set: false }
      });
    case LoginActions.Types.TOKEN_REFRESH:
      return update(state, { loading: { $set: true } });
    case LoginActions.Types.TOKEN_REFRESH_SUCCESS:
      return update(state, {
        $merge: action.data,
        loading: { $set: false }
      });
    case LoginActions.Types.LOGOUT:
      return notLoggedInStatus;
    case LoginActions.Types.PASSWORD_FORGOTTEN_SUCCESS:
      return update(state, {
        succeeded: { $set: true },
        error: { $set: null }
      });
    case LoginActions.Types.PASSWORD_FORGOTTEN_FAILURE:
      return update(state, {
        succeeded: { $set: false },
        error: { $set: action.error }
      });
    case LoginActions.Types.PASSWORD_RESET_TOKEN_VALIDATION_SUCCESS:
      return update(state, {
        succeeded: { $set: true },
        error: { $set: null }
      });
    case LoginActions.Types.PASSWORD_RESET_TOKEN_VALIDATION_FAILURE:
      return update(state, {
        succeeded: { $set: false },
        error: { $set: action.error }
      });
    case LoginActions.Types.PASSWORD_RESET_SUCCESS:
      return update(state, {
        succeeded: { $set: true },
        error: { $set: null }
      });
    case LoginActions.Types.PASSWORD_RESET_FAILURE:
      return update(state, {
        error: { $set: action.error }
      });
    case LoginActions.Types.CLEAR_ERROR_MESSAGE:
      return update(state, {
        error: { $set: null }
      });
    case LoginActions.Types.CLEAR_SUCCESS_MESSAGE:
      return update(state, {
        succeeded: { $set: false }
      });
    default:
      return state;
  }
}
