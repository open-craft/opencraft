import update from 'immutability-helper';
import { RegistrationSteps } from 'global/constants';
import * as RegistrationActions from './actions';
import { blankRegistrationState, RegistrationStateModel } from './models';

export const initialState: Readonly<RegistrationStateModel> = blankRegistrationState;

export function registrationReducer(
  state = initialState,
  action: RegistrationActions.ActionTypes
): RegistrationStateModel {
  switch (action.type) {
    case RegistrationActions.Types.CLEAR_ERROR_MESSAGE:
      // Merge state without erasing previous values
      return update(state, {
        registrationFeedback: { [action.field]: { $set: '' } }
      });
    case RegistrationActions.Types.REGISTRATION_VALIDATION:
      return update(state, { loading: { $set: true } });
    case RegistrationActions.Types.REGISTRATION_VALIDATION_SUCCESS: {
      const newState = {
        ...state,
        loading: false,
        registrationData: {
          ...state.registrationData,
          ...action.data
        }
      };
      if (action.nextStep) {
        newState.currentRegistrationStep = action.nextStep;
      }
      // Merge state without erasing previous values
      return newState;
    }
    case RegistrationActions.Types.REGISTRATION_VALIDATION_FAILURE:
      return {
        ...state,
        registrationFeedback: { ...action.error },
        loading: false
      };
    case RegistrationActions.Types.REGISTRATION_SUBMIT:
      return update(state, { loading: { $set: true } });
    case RegistrationActions.Types.REGISTRATION_FAILURE:
      return {
        ...state,
        loading: false,
        registrationFeedback: { ...action.error }
      };
    case RegistrationActions.Types.REGISTRATION_SUCCESS:
      // Merge state without erasing previous values
      return {
        ...state,
        loading: false,
        currentRegistrationStep: RegistrationSteps.CONGRATS,
        registrationData: {
          ...state.registrationData,
          ...action.data
        }
      };
    case RegistrationActions.Types.GO_TO_NEXT_STEP:
      return update(state, {
        currentRegistrationStep: { $set: action.nextStep }
      });
    default:
      return state;
  }
}
