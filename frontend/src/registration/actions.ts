import { push } from 'connected-react-router';
import { OcimThunkAction } from 'global/types';
import { Action } from 'redux';
import { Types as UIActionTypes } from 'ui/actions';
import { V2Api } from 'global/api';
import { toCamelCase } from 'utils/string_utils';
import {
  RegistrationModel,
  RegistrationStateModel,
  RegistrationFeedbackModel
} from './models';
import { performLogin } from 'auth/actions';

export enum Types {
  // Support action to update root state and clean error messages when users change fields
  CLEAR_ERROR_MESSAGE = 'CLEAR_ERROR_MESSAGE',
  // Data validation actions
  REGISTRATION_VALIDATION = 'REGISTRATION_VALIDATION',
  REGISTRATION_VALIDATION_SUCCESS = 'REGISTRATION_VALIDATION_SUCCESS',
  REGISTRATION_VALIDATION_FAILURE = 'REGISTRATION_VALIDATION_FAILURE',
  // Account registration
  REGISTRATION_SUBMIT = 'REGISTRATION_SUBMIT',
  REGISTRATION_SUCCESS = 'REGISTRATION_SUCCESS',
  REGISTRATION_FAILURE = 'REGISTRATION_FAILURE'
}

export interface FeedbackMessageChange extends Action {
  readonly type: Types.CLEAR_ERROR_MESSAGE;
  readonly field: keyof RegistrationStateModel;
}

export interface RegistrationValidation extends Action {
  readonly type: Types.REGISTRATION_VALIDATION;
}

export interface RegistrationValidationSuccess extends Action {
  readonly type: Types.REGISTRATION_VALIDATION_SUCCESS;
  readonly data: RegistrationModel;
}

export interface RegistrationValidationFailure extends Action {
  readonly type: Types.REGISTRATION_VALIDATION_FAILURE;
  readonly error: RegistrationFeedbackModel;
}

export interface SubmitRegistration extends Action {
  readonly type: Types.REGISTRATION_SUBMIT;
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
  | FeedbackMessageChange
  | RegistrationValidation
  | RegistrationValidationSuccess
  | RegistrationValidationFailure
  | SubmitRegistration
  | RegistrationSuccess
  | RegistrationFailure;

export const clearErrorMessage = (
  field: keyof RegistrationStateModel
) => async (dispatch: any) => {
  dispatch({
    type: Types.CLEAR_ERROR_MESSAGE,
    field
  });
};

export const performValidationAndStore = (
  data: RegistrationModel,
  nextStep?: string
): OcimThunkAction<void> => async dispatch => {
  dispatch({
    type: Types.REGISTRATION_VALIDATION,
    data
  });
  const registrationData: any = { ...data };

  V2Api.instancesOpenedxConfigValidate({
    data: { ...registrationData }
  }).then(() => {
    // If validation succeeds, then save data and go to next step
    dispatch({ type: Types.REGISTRATION_VALIDATION_SUCCESS, data });
    if (nextStep) {
      dispatch(push(nextStep));
    }
    dispatch({ type: UIActionTypes.NAVIGATE_NEXT_PAGE });
  })
  .catch((e: any) => {
    e.json().then((feedback: any) => {
      // If validation fails, return error to form through state
      const error = { ...feedback };
      // Loop at each error message and join them.
      // Also convert keys from snake_case to camelCase
      Object.keys(error).forEach(key => {
        error[toCamelCase(key)] = error[key].join();
      });
      dispatch({
        type: Types.REGISTRATION_VALIDATION_FAILURE,
        error
      });
    });
  });
};


export const submitRegistration = (
  data: RegistrationModel,
  nextStep?: string
): OcimThunkAction<void> => async dispatch => {
  const registrationData: any = { ...data };
  let registrationFeedback: any = {};

  // Check for privacy policy and replace by current date
  if (registrationData.acceptTOS) {
    delete registrationData.acceptTOS
    registrationData.acceptedPrivacyPolicy = new Date();
  } else {
    registrationFeedback.acceptTOS = "You must accept the Terms of Service and Privacy policy."
  }

  // Check if password confirmation is correct
  if (registrationData.password === registrationData.passwordConfirm) {
    delete registrationData.passwordConfirm
  } else {
    registrationFeedback.passwordConfirm = "The password confirmation should match the password from the field above."
  }

  if (Object.entries(registrationFeedback).length === 0) {
    V2Api.accountsCreate({
      data: { ...registrationData }
    }).then(() => {
      // Perform authentication and create new instance
      let x = dispatch(performLogin({
        username: registrationData.username,
        password: registrationData.password
      }));
      console.log(x)
      // dispatch({ type: Types.REGISTRATION_VALIDATION_SUCCESS, data });
      // if (nextStep) {
      //   dispatch(push(nextStep));
      // }
      // dispatch({ type: UIActionTypes.NAVIGATE_NEXT_PAGE });
    })
    .catch((e: any) => {
      e.json().then((feedback: any) => {
        // If validation fails, return error to form through state
        const error = { ...feedback };
        // Loop at each error message and join them.
        // Also convert keys from snake_case to camelCase
        Object.keys(error).forEach(key => {
          error[toCamelCase(key)] = error[key].join();
        });
        dispatch({
          type: Types.REGISTRATION_VALIDATION_FAILURE,
          error
        });
      });
    });
  } else {
    // Failing local validation
    dispatch({
      type: Types.REGISTRATION_VALIDATION_FAILURE,
      error: {...registrationFeedback}
    });
  }
};
