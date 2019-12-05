import * as RegistrationActions from './actions';
import { blankRegistrationState, RegistrationStateModel } from './models';

export const initialState: Readonly<RegistrationStateModel> = blankRegistrationState;

export function registrationReducer(
  state = initialState,
  action: RegistrationActions.ActionTypes
): RegistrationStateModel {
  switch (action.type) {
    case RegistrationActions.Types.ROOT_STATE_UPDATE:
      return {
        ...state,
        ...action.data
      };
    case RegistrationActions.Types.REGISTRATION_VALIDATION:
      return {
        ...state,
        ...action.data,
        loading: true
      };
    case RegistrationActions.Types.REGISTRATION_VALIDATION_SUCCESS:
      return {
        ...state,
        ...action.data,
        loading: false
      };
    case RegistrationActions.Types.REGISTRATION_VALIDATION_FAILURE:
      console.log(action);
      return {
        ...state,
        registrationFeedback: { ...action.error },
        loading: false
      };
    case RegistrationActions.Types.REGISTRATION_SUBMIT:
      return {
        ...state,
        loading: true,
      };
    case RegistrationActions.Types.REGISTRATION_FAILURE:
      return {
        ...state,
        loading: false,
        registrationFeedback: {
          domain: 'This domain already exists!'
        }
      };
    case RegistrationActions.Types.REGISTRATION_SUCCESS:
    console.log('registration ok')
      return {
        ...state,
        ...action.data,
        loading: false
      };
    default:
      return state;
  }
}
