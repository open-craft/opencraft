import { push } from 'connected-react-router';
import { OcimThunkAction } from 'global/types';
import { Action } from 'redux';
import { V2Api } from 'global/api';
import { sanitizeErrorFeedback } from 'utils/string_utils';
import { performLogin } from 'auth/actions';
import {
  RegistrationSteps,
  REGISTRATION_STEPS,
  ROUTES
} from 'global/constants';
import {
  RegistrationModel,
  RegistrationStateModel,
  RegistrationFeedbackModel
} from './models';

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
  REGISTRATION_FAILURE = 'REGISTRATION_FAILURE',
  GO_TO_NEXT_STEP = 'GO_TO_NEXT_STEP'
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
  readonly nextStep?: RegistrationSteps;
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

export interface GoToNextStep extends Action {
  readonly type: Types.GO_TO_NEXT_STEP;
  readonly nextStep: RegistrationSteps;
}

export type ActionTypes =
  | FeedbackMessageChange
  | RegistrationValidation
  | RegistrationValidationSuccess
  | RegistrationValidationFailure
  | SubmitRegistration
  | RegistrationSuccess
  | RegistrationFailure
  | GoToNextStep;

export const clearErrorMessage = (
  field: keyof RegistrationStateModel
) => async (dispatch: any) => {
  dispatch({
    type: Types.CLEAR_ERROR_MESSAGE,
    field
  });
};

export const goToNextStep = (nextStep: RegistrationSteps) => async (
  dispatch: any
) => {
  dispatch({ type: Types.GO_TO_NEXT_STEP, nextStep });
  dispatch(push(REGISTRATION_STEPS[nextStep]));
};

export const performValidationAndStore = (
  data: RegistrationModel,
  nextStep?: RegistrationSteps
): OcimThunkAction<void> => async dispatch => {
  dispatch({
    type: Types.REGISTRATION_VALIDATION,
    data
  });

  V2Api.instancesOpenedxConfigValidate({ data })
    .then(() => {
      // If validation succeeds, then save data and go to next step
      dispatch({ type: Types.REGISTRATION_VALIDATION_SUCCESS, data, nextStep });
      if (nextStep) {
        dispatch(push(REGISTRATION_STEPS[nextStep]));
      }
    })
    .catch((e: any) => {
      try {
        e.json().then((feedback: any) => {
          // If validation fails, return error to form through state
          const error: any = sanitizeErrorFeedback(feedback);
          dispatch({
            type: Types.REGISTRATION_VALIDATION_FAILURE,
            error
          });
        });
      } catch (error) {
        dispatch(push(ROUTES.Error.UNKNOWN_ERROR));
      }
    });
};

export const submitRegistration = (
  userData: RegistrationModel,
  instanceData: RegistrationModel,
  nextStep?: RegistrationSteps
): OcimThunkAction<void> => async (dispatch: any) => {
  dispatch({
    type: Types.REGISTRATION_SUBMIT
  });

  const userRegistrationData: any = { ...userData };
  const registrationFeedback: any = {};

  // Check for privacy policy and replace by current date
  if (userRegistrationData.acceptTOS) {
    delete userRegistrationData.acceptTOS;
    userRegistrationData.acceptedPrivacyPolicy = new Date();
  } else {
    registrationFeedback.acceptTOS =
      'You must accept the Terms of Service and Privacy policy.';
  }

  // Check if password confirmation is correct
  if (userRegistrationData.password === userRegistrationData.passwordConfirm) {
    delete userRegistrationData.passwordConfirm;
  } else {
    registrationFeedback.passwordConfirm =
      'The password confirmation should match the password from the field above.';
  }

  if (Object.entries(registrationFeedback).length === 0) {
    try {
      await V2Api.accountsCreate({ data: userRegistrationData });
      // Perform authentication and create new instance
      try {
        await dispatch(
          performLogin({
            username: userRegistrationData.username,
            password: userRegistrationData.password
          })
        );

        try {
          const sanitizedData = { ...instanceData };
          // Don't send external domain if not using one
          if (sanitizedData.externalDomain === '') {
            delete sanitizedData.externalDomain;
          }
          // Create instance
          await V2Api.instancesOpenedxConfigCreate({ data: sanitizedData });

          dispatch({
            type: Types.REGISTRATION_VALIDATION_SUCCESS,
            data: userData,
            nextStep
          });
          if (nextStep) {
            dispatch(push(REGISTRATION_STEPS[nextStep]));
          }
        } catch (e) {
          dispatch(push(ROUTES.Error.UNKNOWN_ERROR));
        }
      } catch (e) {
        dispatch(push(ROUTES.Error.UNKNOWN_ERROR));
      }
    } catch (e) {
      e.json().then((feedback: any) => {
        // If validation fails, return error to form through state
        const error: any = sanitizeErrorFeedback(feedback);
        dispatch({
          type: Types.REGISTRATION_VALIDATION_FAILURE,
          error
        });
      });
    }
  } else {
    // Failing local validation
    dispatch({
      type: Types.REGISTRATION_VALIDATION_FAILURE,
      error: registrationFeedback
    });
  }
};
