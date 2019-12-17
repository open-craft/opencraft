import * as LoginActions from './actions';
import { notLoggedInStatus, LoginStateModel } from './models';

export const initialState: Readonly<LoginStateModel> = notLoggedInStatus;

export function registrationReducer(
  state = initialState,
  action: LoginActions.ActionTypes
): LoginStateModel {
  switch (action.type) {
    case LoginActions.Types.LOGIN_SUBMIT:
      return state;
    case LoginActions.Types.LOGOUT:
      return notLoggedInStatus;
    default:
      return state;
  }
}
