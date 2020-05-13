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
  logo?: string;
  favicon?: string;
  heroCoverImage: null | string;
}

export interface DeploymentInfoModel {
  status: OpenEdXInstanceDeploymentStatusStatusEnum;
  type: OpenEdXInstanceDeploymentStatusDeploymentTypeEnum;
  undeployedChanges: Array<Array<object>>;
  deployedChanges: Array<Array<object>> | null;
}

// The loading key is used to store field names that are being updated through
// a request. This allows us to individually update fields.
export interface InstancesModel {
  loading: boolean;
  activeInstance: {
    data: InstanceSettingsModel | null;
    feedback: Partial<InstanceSettingsModel>;
    loading: Array<keyof InstanceSettingsModel | 'deployment'>;
    deployment: DeploymentInfoModel | undefined;
  };
  instances: Array<InstanceSettingsModel>;
}

export const initialConsoleState: Readonly<InstancesModel> = {
  loading: false,
  activeInstance: {
    data: null,
    feedback: {},
    loading: [],
    deployment: undefined
  },
  instances: []
};
