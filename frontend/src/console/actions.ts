import { OcimThunkAction } from 'global/types';
import { Action } from 'redux';
import { push } from 'connected-react-router';
import { V2Api } from 'global/api';
import { InstanceSettingsModel, DeploymentInfoModel } from 'console/models';
import { ThemeSchema, StaticContentOverrides } from 'ocim-client';
import { ROUTES } from 'global/constants';
import { sanitizeErrorFeedback } from 'utils/string_utils';

export enum Types {
  // Support action to update root state and clean error messages when users change fields
  CLEAR_ERROR_MESSAGE = 'CLEAR_ERROR_MESSAGE',
  CLEAR_CONSOLE_DATA = 'CLEAR_CONSOLE_DATA',
  // To handle multiple user instances
  USER_INSTANCE_LIST = 'USER_INSTANCE_LIST',
  USER_INSTANCE_LIST_SUCCESS = 'USER_INSTANCE_LIST_SUCCESS',
  USER_INSTANCE_LIST_FAILURE = 'USER_INSTANCE_LIST_FAILURE',
  // Update instance info
  UPDATE_INSTANCE_INFO = 'UPDATE_INSTANCE_INFO',
  UPDATE_INSTANCE_INFO_SUCCESS = 'UPDATE_INSTANCE_INFO_SUCCESS',
  UPDATE_INSTANCE_INFO_FAILURE = 'UPDATE_INSTANCE_INFO_FAILURE',
  UPDATE_INSTANCE_IMAGES = 'UPDATE_INSTANCE_IMAGES',
  UPDATE_INSTANCE_IMAGES_SUCCESS = 'UPDATE_INSTANCE_IMAGES_SUCCESS',
  UPDATE_INSTANCE_IMAGES_FAILURE = 'UPDATE_INSTANCE_IMAGES_FAILURE',
  // Theming specific actions
  UPDATE_INSTANCE_THEME = 'UPDATE_INSTANCE_THEME',
  UPDATE_INSTANCE_THEME_SUCCESS = 'UPDATE_INSTANCE_THEME_SUCCESS',
  UPDATE_INSTANCE_THEME_FAILURE = 'UPDATE_INSTANCE_THEME_FAILURE',
  // Static content overrides actions
  UPDATE_INSTANCE_STATIC_CONTENT_OVERRIDES = 'UPDATE_INSTANCE_STATIC_CONTENT_OVERRIDES',
  UPDATE_INSTANCE_STATIC_CONTENT_OVERRIDES_SUCCESS = 'UPDATE_INSTANCE_STATIC_CONTENT_OVERRIDES_SUCCESS',
  UPDATE_INSTANCE_STATIC_CONTENT_OVERRIDES_FAILURE = 'UPDATE_INSTANCE_STATIC_CONTENT_OVERRIDES_FAILURE',

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

export interface ClearFeedbackMessage extends Action {
  readonly type: Types.CLEAR_ERROR_MESSAGE;
  readonly field: keyof InstanceSettingsModel;
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

export interface UpdateInstanceImages extends Action {
  readonly type: Types.UPDATE_INSTANCE_IMAGES;
  readonly fieldName: keyof InstanceSettingsModel;
}

export interface UpdateInstanceImagesSuccess extends Action {
  readonly type: Types.UPDATE_INSTANCE_IMAGES_SUCCESS;
  readonly data: Partial<InstanceSettingsModel>;
}

export interface UpdateInstanceImagesFailure extends Action {
  readonly type: Types.UPDATE_INSTANCE_IMAGES_FAILURE;
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

export interface UpdateInstanceStaticContentOverrides extends Action {
  readonly type: Types.UPDATE_INSTANCE_STATIC_CONTENT_OVERRIDES;
  readonly data: Partial<StaticContentOverrides>;
}

export interface UpdateInstanceStaticContentOverridesSuccess extends Action {
  readonly type: Types.UPDATE_INSTANCE_STATIC_CONTENT_OVERRIDES_SUCCESS;
  readonly data: Partial<StaticContentOverrides>;
}

export interface UpdateInstanceStaticContentOverridesFailure extends Action {
  readonly type: Types.UPDATE_INSTANCE_STATIC_CONTENT_OVERRIDES_FAILURE;
  readonly data: Partial<StaticContentOverrides>;
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

export interface ClearConsoleData extends Action {
  readonly type: Types.CLEAR_CONSOLE_DATA;
  readonly data: Array<InstanceSettingsModel>;
}

export type ActionTypes =
  | ClearFeedbackMessage
  | ClearConsoleData
  | UserInstanceList
  | UserInstanceListSuccess
  | UserInstanceListFailure
  | UpdateInstanceInfo
  | UpdateInstanceInfoSuccess
  | UpdateInstanceInfoFailure
  | UpdateInstanceImages
  | UpdateInstanceImagesSuccess
  | UpdateInstanceImagesFailure
  | UpdateInstanceStaticContentOverrides
  | UpdateInstanceStaticContentOverridesSuccess
  | UpdateInstanceStaticContentOverridesFailure
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

export const clearErrorMessage = (field: keyof InstanceSettingsModel) => async (
  dispatch: any
) => {
  dispatch({
    type: Types.CLEAR_ERROR_MESSAGE,
    field
  });
};

export const clearConsoleData = (): OcimThunkAction<void> => async dispatch => {
  dispatch({
    type: Types.CLEAR_CONSOLE_DATA
  });
};

export const listUserInstances = (): OcimThunkAction<
  void
> => async dispatch => {
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

export const updateImages = (
  instanceId: number,
  imageFieldName: string,
  file: null | string
): OcimThunkAction<void> => async (dispatch, getState) => {
  // Dispatch variable lock to avoid sending a second image
  // while the first one is still being transmitted
  dispatch({
    type: Types.UPDATE_INSTANCE_INFO,
    imageFieldName
  });

  try {
    const response: {
      [key: string]: any;
    } = await V2Api.instancesOpenedxConfigImage({
      id: String(instanceId),
      [imageFieldName]: file
    });

    const { activeInstance } = getState().console;
    if (activeInstance.data && activeInstance.data.id === instanceId) {
      dispatch({
        type: Types.UPDATE_INSTANCE_INFO_SUCCESS,
        data: {
          [imageFieldName]: response[imageFieldName]
        }
      });
    }
  } catch (e) {
    try {
      const error = await e.json();

      dispatch({
        type: Types.UPDATE_INSTANCE_INFO_FAILURE,
        data: sanitizeErrorFeedback(error)
      });
    } catch {
      dispatch(push(ROUTES.Error.UNKNOWN_ERROR));
    }
  }
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

export const updateStaticContentOverridesFieldValue = (
  instanceId: number,
  fieldName: string,
  value: string
): OcimThunkAction<void> => async (dispatch, getState) => {
  dispatch({
    type: Types.UPDATE_INSTANCE_STATIC_CONTENT_OVERRIDES,
    fieldName
  });
  try {
    const response = await V2Api.instancesOpenedxConfigStaticContentOverrides({
      id: String(instanceId),
      data: {
        [fieldName]: value
      }
    });

    const { activeInstance } = getState().console;
    if (activeInstance.data && activeInstance.data.id === instanceId) {
      dispatch({
        type: Types.UPDATE_INSTANCE_STATIC_CONTENT_OVERRIDES_SUCCESS,
        data: response
      });
    }
  } catch {
    dispatch({
      type: Types.UPDATE_INSTANCE_STATIC_CONTENT_OVERRIDES_FAILURE,
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
