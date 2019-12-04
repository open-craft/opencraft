import * as RegistrationActions from './actions';
import { blankRegistration, RegistrationModel } from './models';

export const initialState: Readonly<RegistrationModel> = blankRegistration;

export function registrationReducer(
  state = initialState,
  action: RegistrationActions.ActionTypes
): RegistrationModel {
  switch (action.type) {
    case RegistrationActions.Types.REGISTRATION_SUBMIT:
      return {
        ...state,
        loading: true,
        domainError: ''
      };
    case RegistrationActions.Types.REGISTRATION_FAILURE:
      return {
        ...state,
        loading: false,
        // TODO: Internationalize this
        domainError: 'This domain already exists!'
      };
    case RegistrationActions.Types.REGISTRATION_SUCCESS:
    console.log(action.data)
      return {
        ...state,
        ...action.data,
        loading: false,
      };
    default:
      return state;
  }
}
