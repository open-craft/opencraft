import { OcimThunkAction } from 'global/types';
import { Action } from 'redux';
import { V2Api } from 'global/api';
import { InstanceSettingsModel, DeploymentInfoModel } from 'console/models';

export enum Types {
  // Support action to update root state and clean error messages when users change fields
  CLEAR_ERROR_MESSAGE = 'CLEAR_ERROR_MESSAGE',
  // To handle multiple user instances
  USER_INSTANCE_LIST = 'USER_INSTANCE_LIST',
  USER_INSTANCE_LIST_SUCCESS = 'USER_INSTANCE_LIST_SUCCESS',
  USER_INSTANCE_LIST_FAILURE = 'USER_INSTANCE_LIST_FAILURE',
  // Update instance info
  UPDATE_INSTANCE_INFO = 'UPDATE_INSTANCE_INFO',
  UPDATE_INSTANCE_INFO_SUCCESS = 'UPDATE_INSTANCE_INFO_SUCCESS',
  UPDATE_INSTANCE_INFO_FAILURE = 'UPDATE_INSTANCE_INFO_FAILURE',
  // Redeployment related actions
  GET_DEPLOYMENT_STATUS = 'GET_DEPLOYMENT_STATUS',
  GET_DEPLOYMENT_STATUS_SUCCESS = 'GET_DEPLOYMENT_STATUS_SUCCESS',
  GET_DEPLOYMENT_STATUS_FAILURE = 'GET_DEPLOYMENT_STATUS_FAILURE',
  PERFORM_DEPLOYMENT = 'PERFORM_DEPLOYMENT',
  PERFORM_DEPLOYMENT_SUCCESS = 'PERFORM_DEPLOYMENT_SUCCESS',
  PERFORM_DEPLOYMENT_FAILURE = 'PERFORM_DEPLOYMENT_FAILURE'
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

export interface UpdateInstanceInfo extends Action {
  readonly type: Types.UPDATE_INSTANCE_INFO;
  readonly fieldName: keyof InstanceSettingsModel;
}

export interface UpdateInstanceInfoSuccess extends Action {
  readonly type: Types.UPDATE_INSTANCE_INFO_SUCCESS;
  readonly data: Partial<InstanceSettingsModel>;
}

export interface UpdateInstanceInfoFailure extends Action {
  readonly type: Types.UPDATE_INSTANCE_INFO_FAILURE;
  readonly data: Partial<InstanceSettingsModel>;
}

export interface GetDeploymentStatus extends Action {
  readonly type: Types.GET_DEPLOYMENT_STATUS;
  readonly instanceId: number;
}

export interface GetDeploymentStatusSuccess extends Action {
  readonly type: Types.GET_DEPLOYMENT_STATUS_SUCCESS;
  readonly data: DeploymentInfoModel;
}

export interface GetDeploymentStatusFailure extends Action {
  readonly type: Types.GET_DEPLOYMENT_STATUS_FAILURE;
  readonly errors: any;
}

export interface PerformDeployment extends Action {
  readonly type: Types.PERFORM_DEPLOYMENT;
  readonly instanceId: number;
}

export interface PerformDeploymentSuccess extends Action {
  readonly type: Types.PERFORM_DEPLOYMENT_SUCCESS;
}

export interface PerformDeploymentFailure extends Action {
  readonly type: Types.PERFORM_DEPLOYMENT_FAILURE;
  readonly errors: any;
}

export type ActionTypes =
  | UserInstanceList
  | UserInstanceListSuccess
  | UserInstanceListFailure
  | UpdateInstanceInfo
  | UpdateInstanceInfoSuccess
  | UpdateInstanceInfoFailure
  | GetDeploymentStatus
  | GetDeploymentStatusSuccess
  | GetDeploymentStatusFailure
  | PerformDeployment
  | PerformDeploymentSuccess
  | PerformDeploymentFailure;

export const listUserInstances = (): OcimThunkAction<void> => async dispatch => {
  dispatch({ type: Types.USER_INSTANCE_LIST });

  V2Api.instancesOpenedxConfigList()
    .then((response: any) => {
      dispatch({
        type: Types.USER_INSTANCE_LIST_SUCCESS,
        data: response
      });
    })
    .catch((e: any) => {
      dispatch({
        type: Types.USER_INSTANCE_LIST_FAILURE
      });
    });
};

export const updateFieldValue = (
  instanceId: number,
  fieldName: string,
  value: string
): OcimThunkAction<void> => async dispatch => {
  dispatch({
    type: Types.UPDATE_INSTANCE_INFO,
    fieldName
  });

  setTimeout(function() {
    dispatch({
      type: Types.UPDATE_INSTANCE_INFO_SUCCESS,
      data: {
        [fieldName]: value
      }
    });
    // dispatch({
    //   type: Types.UPDATE_INSTANCE_INFO_FAILURE,
    //   data: {
    //     [fieldName]: value
    //   }
    // });
  }, 2000);

  // After action succeeds, dispatch another action to update redeployment toolbar status
};

export const getDeploymentStatus = (
  instanceId: number
): OcimThunkAction<void> => async dispatch => {
  dispatch({
    type: Types.GET_DEPLOYMENT_STATUS
  });

  setTimeout(function() {
    dispatch({
      type: Types.GET_DEPLOYMENT_STATUS_SUCCESS,
      data: {
        status: 'UP_TO_DATE',
        numberOfChanges: 2
      }
    });
    // dispatch({
    //   type: Types.GET_DEPLOYMENT_STATUS_FAILURE,
    //   data: {
    //     [fieldName]: value
    //   }
    // });
  }, 2000);

  // After action succeeds, dispatch another action to update redeployment toolbar status
};
