import { RedeploymentStatus } from 'global/constants';

export interface InstanceSettingsModel {
  [key: string]: string | number;
  id: number;
  subdomain: string;
  instanceName: string;
  publicContactEmail: string;
  privacyPolicyUrl: string;
}

export interface DeploymentInfoModel {
  status: RedeploymentStatus;
  numberOfChanges: number;
}

// The loading key is used to store field names that are being updated through
// a request. This allows us to individually update fields.
export interface InstancesModel {
  loading: boolean;
  activeInstance: {
    data: InstanceSettingsModel | null;
    feedback: Partial<InstanceSettingsModel>;
    loading: Array<keyof InstanceSettingsModel>;
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
