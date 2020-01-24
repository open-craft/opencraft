export interface InstanceSettingsModel {
  id: number | null;
  subdomain: string | null;
  instanceName: string | null;
  publicContactEmail: string | null;
  privacyPolicyUrl: string | null;
}

export interface InstancesModel {
  loading: boolean;
  selectedInstance: number | null;
  instances: Array<InstanceSettingsModel>;
}

export const initialConsoleState: Readonly<InstancesModel> = {
  loading: false,
  selectedInstance: null,
  instances: []
};
