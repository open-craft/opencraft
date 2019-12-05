import { push } from 'connected-react-router';
import { OcimThunkAction } from 'global/types';
import { Action } from 'redux';
import { Types as UIActionTypes } from 'ui/actions';
import {
  RegistrationModel,
  RegistrationStateModel,
  RegistrationFeedbackModel
} from './models';

export enum Types {
  // Support action to update root state
  ROOT_STATE_UPDATE = 'ROOT_STATE_UPDATE',
  // Data validation actions
  REGISTRATION_VALIDATION = 'REGISTRATION_VALIDATION',
  REGISTRATION_VALIDATION_SUCCESS = 'REGISTRATION_VALIDATION_SUCCESS',
  REGISTRATION_VALIDATION_FAILURE = 'REGISTRATION_VALIDATION_FAILURE',
  // Account registration
  REGISTRATION_SUBMIT = 'REGISTRATION_SUBMIT',
  REGISTRATION_SUCCESS = 'REGISTRATION_SUCCESS',
  REGISTRATION_FAILURE = 'REGISTRATION_FAILURE'
}

export interface RootStateUpdate extends Action {
  readonly type: Types.ROOT_STATE_UPDATE;
  readonly data: RegistrationStateModel;
}

export interface RegistrationValidation extends Action {
  readonly type: Types.REGISTRATION_VALIDATION;
  readonly data: RegistrationStateModel;
}

export interface RegistrationValidationSuccess extends Action {
  readonly type: Types.REGISTRATION_VALIDATION_SUCCESS;
  readonly data: RegistrationStateModel;
}

export interface RegistrationValidationFailure extends Action {
  readonly type: Types.REGISTRATION_VALIDATION_FAILURE;
  readonly error: RegistrationFeedbackModel;
}

export interface SubmitRegistration extends Action {
  readonly type: Types.REGISTRATION_SUBMIT;
  readonly data: RegistrationStateModel;
}

export interface RegistrationSuccess extends Action {
  readonly type: Types.REGISTRATION_SUCCESS;
  readonly data: RegistrationStateModel;
}

export interface RegistrationFailure extends Action {
  readonly type: Types.REGISTRATION_FAILURE;
  readonly error: RegistrationFeedbackModel;
}

export type ActionTypes =
  | RootStateUpdate
  | RegistrationValidation
  | RegistrationValidationSuccess
  | RegistrationValidationFailure
  | SubmitRegistration
  | RegistrationSuccess
  | RegistrationFailure;

export const updateRootState = (
  data: RegistrationModel
): OcimThunkAction<void> => async dispatch => {
  dispatch({ type: Types.ROOT_STATE_UPDATE, data });
};

export const performValidation = (
  data: RegistrationModel,
  nextStep?: string
): OcimThunkAction<void> => async dispatch => {
  // Placeholder for form validation method
  dispatch({
    type: Types.REGISTRATION_VALIDATION,
    data
  });
  setTimeout(() => {
    try {
      // TODO
      if (data.domain === 'existing') {
        throw Error('Test error');
      }
      dispatch({ type: Types.REGISTRATION_VALIDATION_SUCCESS, data });
      if (nextStep) {
        dispatch(push(nextStep));
      }
      dispatch({ type: UIActionTypes.NAVIGATE_NEXT_PAGE });
    } catch (e) {
      const error = {
        domain: 'Domain already exists!'
      };
      dispatch({
        type: Types.REGISTRATION_VALIDATION_FAILURE,
        error
      });
    }
  }, 800);
};

export const submitRegistration = (
  data: RegistrationModel,
  nextStep?: string
): OcimThunkAction<void> => async dispatch => {
  // Placeholder for form submit method
  dispatch({
    type: Types.REGISTRATION_SUBMIT,
    data
  });

  setTimeout(() => {
    try {
      // TODO
      if (data.domain === 'existing') {
        throw Error('Test error');
      }
      dispatch({ type: Types.REGISTRATION_SUCCESS, data });
      if (nextStep) {
        dispatch(push(nextStep));
      }
      dispatch({ type: UIActionTypes.NAVIGATE_NEXT_PAGE });
    } catch (error) {
      dispatch({
        type: Types.REGISTRATION_FAILURE,
        error
      });
    }
  }, 800);
};
