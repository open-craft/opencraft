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
      return state;
    case LoginActions.Types.LOGIN_SUCCESS:
      return update(state, { $merge: action.data });
    case LoginActions.Types.LOGIN_FAILURE:
      return update(state, { error: { $set: action.error } });
    case LoginActions.Types.LOGOUT:
      return notLoggedInStatus;
    default:
      return state;
  }
}
