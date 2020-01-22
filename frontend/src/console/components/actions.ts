import { OcimThunkAction } from 'global/types';
import { Action } from 'redux';
import { RedeploymentStatusModel } from './models';

export enum Types {
  // Support action to update root state and clean error messages when users change fields
  CLEAR_ERROR_MESSAGE = 'CLEAR_ERROR_MESSAGE',
  // Redeployment related action types
  REDEPLOYMENT_STATUS = 'REDEPLOYMENT_STATUS',
  REDEPLOYMENT_STATUS_SUCCESS = 'REDEPLOYMENT_STATUS_SUCCESS',
  REDEPLOYMENT_STATUS_FAILURE = 'REDEPLOYMENT_STATUS_FAILURE',
  REDEPLOYMENT_PERFORM = 'REDEPLOYMENT_PERFORM',
  REDEPLOYMENT_PERFORM_SUCCESS = 'REDEPLOYMENT_PERFORM_SUCCESS',
  REDEPLOYMENT_PERFORM_FAILURE = 'REDEPLOYMENT_PERFORM_FAILURE',
  REDEPLOYMENT_CANCEL = 'REDEPLOYMENT_CANCEL',
  REDEPLOYMENT_CANCEL_SUCCESS = 'REDEPLOYMENT_CANCEL_SUCCESS',
  REDEPLOYMENT_CANCEL_FAILURE = 'REDEPLOYMENT_CANCEL_FAILURE'
}

export interface RedeploymentGetStatus extends Action {
  readonly type: Types.REDEPLOYMENT_STATUS;
  readonly instanceId: number;
}

export interface RedeploymentGetStatusSuccess extends Action {
  readonly type: Types.REDEPLOYMENT_STATUS_SUCCESS;
  readonly data: RedeploymentStatusModel;
}

export interface RedeploymentGetStatusFailure extends Action {
  readonly type: Types.REDEPLOYMENT_STATUS_FAILURE;
  readonly error: any;
}

export type ActionTypes =
  | RedeploymentGetStatus
  | RedeploymentGetStatusSuccess
  | RedeploymentGetStatusFailure;

export const performRedeployment = (
  instanceId: number,
): OcimThunkAction<void> => async dispatch => {
  dispatch({
    type: Types.REDEPLOYMENT_STATUS,
    instanceId
  });

  // Placeholder for when redeployment APIs are implemented
};
