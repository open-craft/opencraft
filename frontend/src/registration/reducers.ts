import * as RegistrationActions from './actions';
import { blankRegistration, RegistrationModel } from './models';

export const initialState: Readonly<RegistrationModel> = blankRegistration;

export function registrationReducer(state = initialState,
  action: RegistrationActions.ActionTypes): RegistrationModel {
  switch (action.type) {
    case RegistrationActions.Types.REGISTRATION_SUBMIT:
      return state;
    case RegistrationActions.Types.REGISTRATION_FAILURE:
      return state;
    case RegistrationActions.Types.REGISTRATION_SUCCESS:
      return { ...state, ...action.data };
    default:
      return state;
  }
}
