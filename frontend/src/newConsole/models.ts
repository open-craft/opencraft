import {
  OpenEdXInstanceDeploymentStatusStatusEnum,
  OpenEdXInstanceDeploymentStatusDeploymentTypeEnum,
  StaticContentOverrides,
  ThemeSchema
} from 'ocim-client';

export interface InstanceSettingsModel {
  [key: string]: any | undefined;
  id: number;
  lmsUrl?: string;
  studioUrl?: string;
  subdomain: string;
  instanceName: string;
  publicContactEmail: string;
  privacyPolicyUrl: string;
  draftThemeConfig: undefined | ThemeSchema;
  draftStaticContentOverrides: undefined | StaticContentOverrides;
  staticPagesEnabled: { [k: string]: any };
  logo?: string;
  favicon?: string;
  heroCoverImage: null | string;
}

export interface DeploymentNotificationModel {
  status: OpenEdXInstanceDeploymentStatusStatusEnum;
  deployedChanges: Array<
    Array<Array<Array<number | string> | number> | string>
  > | null;
  date: Date;
}

export interface DeploymentInfoModel {
  status: OpenEdXInstanceDeploymentStatusStatusEnum;
  deploymentType: OpenEdXInstanceDeploymentStatusDeploymentTypeEnum;
  undeployedChanges: Array<
    Array<Array<Array<number | string> | number> | string>
  >;
  deployedChanges: Array<
    Array<Array<Array<number | string> | number> | string>
  > | null;
}

// The loading key is used to store field names that are being updated through
// a request. This allows us to individually update fields.
export interface InstancesModel {
  loading: boolean;
  error: any;
  activeInstance: {
    data: InstanceSettingsModel | null;
    feedback: Partial<InstanceSettingsModel>;
    loading: Array<keyof InstanceSettingsModel | 'deployment'>;
    deployment: DeploymentInfoModel | undefined;
  };
  instances: Array<InstanceSettingsModel>;
  notifications: Array<DeploymentNotificationModel>;
  notificationsLoading: boolean;
}

export const initialConsoleState: Readonly<InstancesModel> = {
  loading: false,
  error: null,
  activeInstance: {
    data: null,
    feedback: {},
    loading: [],
    deployment: undefined
  },
  instances: [],
  notifications: [],
  notificationsLoading: false
};
