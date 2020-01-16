import update from 'immutability-helper';
import * as LoginActions from './actions';
import { notLoggedInStatus, LoginStateModel } from './models';

export const initialState: Readonly<LoginStateModel> = notLoggedInStatus;

export function loginStateReducer(
  state = initialState,
  action: LoginActions.ActionTypes
): LoginStateModel {
  switch (action.type) {
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
    default:
      return state;
  }
}
