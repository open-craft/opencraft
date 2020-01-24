import { OcimThunkAction } from 'global/types';
import { Action } from 'redux';
import { V2Api } from 'global/api';
import { InstanceSettingsModel } from 'console/models';

export enum Types {
  // Support action to update root state and clean error messages when users change fields
  CLEAR_ERROR_MESSAGE = 'CLEAR_ERROR_MESSAGE',
  // To handle multiple user instances
  USER_INSTANCE_LIST = 'USER_INSTANCE_LIST',
  USER_INSTANCE_LIST_SUCCESS = 'USER_INSTANCE_LIST_SUCCESS',
  USER_INSTANCE_LIST_FAILURE = 'USER_INSTANCE_LIST_FAILURE',
}

export interface UserInstanceList extends Action {
  readonly type: Types.USER_INSTANCE_LIST;
}

export interface UserInstanceListSuccess extends Action {
  readonly type: Types.USER_INSTANCE_LIST_SUCCESS;
  readonly data: Array<InstanceSettingsModel>;
}

export interface UserInstanceListFailure extends Action {
  readonly type: Types.USER_INSTANCE_LIST_FAILURE;
  readonly error: any;
}

export type ActionTypes =
  | UserInstanceList
  | UserInstanceListSuccess
  | UserInstanceListFailure;

export const listUserInstances = (
  instanceId: number,
): OcimThunkAction<void> => async dispatch => {
  dispatch({ type: Types.USER_INSTANCE_LIST });

  V2Api.instancesOpenedxConfigList().then((response) => {
    dispatch({
      type: Types.USER_INSTANCE_LIST_SUCCESS,
      data: response
    });
  })
  .catch((e: any) => {
    dispatch({
      type: Types.USER_INSTANCE_LIST_FAILURE,
    });
  });
};
