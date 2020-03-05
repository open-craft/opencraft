import { OcimThunkAction } from 'global/types';
import { Action } from 'redux';
import { V2Api } from 'global/api';
import { InstanceSettingsModel, DeploymentInfoModel } from 'console/models';
import { ThemeSchema } from 'ocim-client';

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
  // Theming specific actions
  UPDATE_INSTANCE_THEME = 'UPDATE_INSTANCE_THEME',
  UPDATE_INSTANCE_THEME_SUCCESS = 'UPDATE_INSTANCE_THEME_SUCCESS',
  UPDATE_INSTANCE_THEME_FAILURE = 'UPDATE_INSTANCE_THEME_FAILURE',
  // Redeployment related actions
  GET_DEPLOYMENT_STATUS = 'GET_DEPLOYMENT_STATUS',
  GET_DEPLOYMENT_STATUS_SUCCESS = 'GET_DEPLOYMENT_STATUS_SUCCESS',
  GET_DEPLOYMENT_STATUS_FAILURE = 'GET_DEPLOYMENT_STATUS_FAILURE',
  PERFORM_DEPLOYMENT = 'PERFORM_DEPLOYMENT',
  PERFORM_DEPLOYMENT_SUCCESS = 'PERFORM_DEPLOYMENT_SUCCESS',
  PERFORM_DEPLOYMENT_FAILURE = 'PERFORM_DEPLOYMENT_FAILURE',
  CANCEL_DEPLOYMENT = 'CANCEL_DEPLOYMENT',
  CANCEL_DEPLOYMENT_SUCCESS = 'CANCEL_DEPLOYMENT_SUCCESS',
  CANCEL_DEPLOYMENT_FAILURE = 'CANCEL_DEPLOYMENT_FAILURE'
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

export interface UpdateThemeConfig extends Action {
  readonly type: Types.UPDATE_INSTANCE_THEME;
  readonly fieldName: keyof ThemeSchema;
}

export interface UpdateThemeConfigSuccess extends Action {
  readonly type: Types.UPDATE_INSTANCE_THEME_SUCCESS;
  readonly data: Partial<ThemeSchema>;
}

export interface UpdateThemeConfigFailure extends Action {
  readonly type: Types.UPDATE_INSTANCE_THEME_FAILURE;
  readonly data: Partial<ThemeSchema>;
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

export interface CancelDeployment extends Action {
  readonly type: Types.CANCEL_DEPLOYMENT;
  readonly instanceId: number;
}

export interface CancelDeploymentSuccess extends Action {
  readonly type: Types.CANCEL_DEPLOYMENT_SUCCESS;
}

export interface CancelDeploymentFailure extends Action {
  readonly type: Types.CANCEL_DEPLOYMENT_FAILURE;
  readonly errors: any;
}

export type ActionTypes =
  | UserInstanceList
  | UserInstanceListSuccess
  | UserInstanceListFailure
  | UpdateInstanceInfo
  | UpdateInstanceInfoSuccess
  | UpdateInstanceInfoFailure
  | UpdateThemeConfig
  | UpdateThemeConfigSuccess
  | UpdateThemeConfigFailure
  | GetDeploymentStatus
  | GetDeploymentStatusSuccess
  | GetDeploymentStatusFailure
  | PerformDeployment
  | PerformDeploymentSuccess
  | PerformDeploymentFailure
  | CancelDeployment
  | CancelDeploymentSuccess
  | CancelDeploymentFailure;

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
): OcimThunkAction<void> => async (dispatch, getState) => {
  dispatch({
    type: Types.UPDATE_INSTANCE_INFO,
    fieldName
  });

  try {
    await V2Api.instancesOpenedxConfigPartialUpdate({
      id: String(instanceId),
      data: { [fieldName]: value }
    });

    const { activeInstance } = getState().console;
    if (activeInstance.data && activeInstance.data.id === instanceId) {
      dispatch({
        type: Types.UPDATE_INSTANCE_INFO_SUCCESS,
        data: {
          [fieldName]: value
        }
      });
    }
  } catch {
    dispatch({
      type: Types.UPDATE_INSTANCE_INFO_FAILURE,
      data: {
        [fieldName]: value
      }
    });
  }
};

export const updateThemeFieldValue = (
  instanceId: number,
  fieldName: string,
  value: string
): OcimThunkAction<void> => async (dispatch, getState) => {
  dispatch({
    type: Types.UPDATE_INSTANCE_THEME,
    fieldName
  });

  try {
    const response = await V2Api.instancesOpenedxConfigThemeConfig({
      id: String(instanceId),
      data: {
        [fieldName]: value
      }
    });

    const { activeInstance } = getState().console;
    if (activeInstance.data && activeInstance.data.id === instanceId) {
      dispatch({
        type: Types.UPDATE_INSTANCE_THEME_SUCCESS,
        data: response
      });
    }
  } catch {
    dispatch({
      type: Types.UPDATE_INSTANCE_THEME_FAILURE,
      data: {
        [fieldName]: value
      }
    });
  }
};

export const getDeploymentStatus = (
  instanceId: number
): OcimThunkAction<void> => async (dispatch, getState) => {
  dispatch({
    type: Types.GET_DEPLOYMENT_STATUS
  });

  try {
    const response = await V2Api.instancesOpenedxDeploymentRead({
      id: String(instanceId)
    });

    const { activeInstance } = getState().console;
    if (activeInstance.data && activeInstance.data.id === instanceId) {
      dispatch({
        type: Types.GET_DEPLOYMENT_STATUS_SUCCESS,
        data: response
      });
    }
  } catch (e) {
    dispatch({
      type: Types.GET_DEPLOYMENT_STATUS_FAILURE,
      errors: e
    });
  }
};

export const performDeployment = (
  instanceId: number
): OcimThunkAction<void> => async (dispatch, getState) => {
  dispatch({
    type: Types.PERFORM_DEPLOYMENT
  });

  try {
    await V2Api.instancesOpenedxDeploymentCreate({
      data: { id: instanceId }
    });

    const { activeInstance } = getState().console;
    if (activeInstance.data && activeInstance.data.id === instanceId) {
      // Just dispatch the successful action, the automatic updates will take
      // care of updating the rest.
      dispatch({ type: Types.PERFORM_DEPLOYMENT_SUCCESS });
    }
  } catch (e) {
    dispatch({
      type: Types.PERFORM_DEPLOYMENT_FAILURE,
      error: e
    });
  }
};

export const cancelDeployment = (
  instanceId: number
): OcimThunkAction<void> => async (dispatch, getState) => {
  dispatch({
    type: Types.CANCEL_DEPLOYMENT
  });

  try {
    await V2Api.instancesOpenedxDeploymentDelete({ id: String(instanceId) });

    const { activeInstance } = getState().console;
    if (activeInstance.data && activeInstance.data.id === instanceId) {
      // Just dispatch the successful action, the automatic updates will take
      // care of updating the rest.
      dispatch({ type: Types.CANCEL_DEPLOYMENT_SUCCESS });
    }
  } catch (e) {
    dispatch({
      type: Types.CANCEL_DEPLOYMENT_FAILURE,
      error: e
    });
  }
};
