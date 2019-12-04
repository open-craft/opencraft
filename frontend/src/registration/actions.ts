import { push } from 'connected-react-router';
import { OcimThunkAction } from 'global/types';
import { Action } from 'redux';
import { Types as UIActionTypes } from 'ui/actions';
import { RegistrationModel, InstanceInfoModel, DomainInfoModel } from './models';

export enum Types {
  REGISTRATION_SUBMIT = 'REGISTRATION_SUBMIT',
  REGISTRATION_SUCCESS = 'REGISTRATION_SUCCESS',
  REGISTRATION_FAILURE = 'REGISTRATION_FAILURE'
}

export interface SubmitRegistration extends Action {
  readonly type: Types.REGISTRATION_SUBMIT;
  readonly data: RegistrationModel;
}

export interface RegistrationSuccess extends Action {
  readonly type: Types.REGISTRATION_SUCCESS;
  readonly data: RegistrationModel;
}

export interface RegistrationFailure extends Action {
  readonly type: Types.REGISTRATION_FAILURE;
  readonly error: any;
}

export type ActionTypes =
  | SubmitRegistration
  | RegistrationSuccess
  | RegistrationFailure;


export const updateDomainInfoState = (
  data: DomainInfoModel,
): OcimThunkAction<void> => async dispatch => {
  dispatch({ type: Types.REGISTRATION_SUCCESS, data });
};

export const updateInstanceInfoState = (
  data: InstanceInfoModel,
): OcimThunkAction<void> => async dispatch => {
  dispatch({ type: Types.REGISTRATION_SUCCESS, data });
};

export const submitRegistration = (
  data: RegistrationModel,
  nextStep?: string
): OcimThunkAction<void> => async dispatch => {
  dispatch({
    type: Types.REGISTRATION_SUBMIT,
    data
  });

  setTimeout(() => {
    try {
      // try submitting form data
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

export const validateInstanceInfo = (
  data: InstanceInfoModel,
  nextStep?: string
): OcimThunkAction<void> => async dispatch => {
  dispatch({
    type: Types.REGISTRATION_SUBMIT,
    data
  });
  setTimeout(() => {
    try {
      // try submitting form data
      // TODO
      if (data.publicContactEmail === 'existing') {
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
