import * as RegistrationActions from './actions';
import { blankRegistrationState, RegistrationStateModel } from './models';

export const initialState: Readonly<RegistrationStateModel> = blankRegistrationState;

export function registrationReducer(
  state = initialState,
  action: RegistrationActions.ActionTypes
): RegistrationStateModel {
  console.log(state);
  switch (action.type) {
    case RegistrationActions.Types.ROOT_STATE_UPDATE:
      // Merge state without erasing previous values
      return {
        loading: state.loading,
        registrationData: {
          ...state.registrationData,
          ...action.data.registrationData
        },
        registrationFeedback: {
          ...state.registrationFeedback,
          ...action.data.registrationFeedback
        }
      };
    case RegistrationActions.Types.REGISTRATION_VALIDATION:
      return {
        ...state,
        loading: true
      };
    case RegistrationActions.Types.REGISTRATION_VALIDATION_SUCCESS:
      // Merge state without erasing previous values
      return {
        ...state,
        loading: false,
        registrationData: {
          ...state.registrationData,
          ...action.data.registrationData
        }
      };
    case RegistrationActions.Types.REGISTRATION_VALIDATION_FAILURE:
      return {
        ...state,
        registrationFeedback: { ...action.error },
        loading: false
      };
    case RegistrationActions.Types.REGISTRATION_SUBMIT:
      return {
        ...state,
        loading: true
      };
    case RegistrationActions.Types.REGISTRATION_FAILURE:
      return {
        ...state,
        loading: false,
        registrationFeedback: { ...action.error }
      };
    case RegistrationActions.Types.REGISTRATION_SUCCESS:
      return {
        ...state,
        loading: false
      };
    default:
      return state;
  }
}
