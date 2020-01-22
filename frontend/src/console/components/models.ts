import { RedeploymentStatus } from './constants'

export interface InstanceSettingsModel {
  internalDomainName: string | null;
  internalStudioDomainName: string | null;
  externalDomainName: string | null;
  externalStudioDomainName: string | null;
  instanceName: string | null;
  publicContactEmail: string | null;
}

export interface RedeploymentStatusModel {
  status: RedeploymentStatus | null;
  numPendingChanges: number | null;
}

export interface InstanceModel {
  instanceSettings: InstanceSettingsModel;
  redeployment: RedeploymentStatusModel;
}

export const initialConsoleState: Readonly<InstanceModel> = {
  redeployment: {
    status: RedeploymentStatus.NO_STATUS,
    numPendingChanges: null
  },
  instanceSettings: {
    internalDomainName: null,
    internalStudioDomainName: null,
    externalDomainName: null,
    externalStudioDomainName: null,
    instanceName: null,
    publicContactEmail: null,
  }
}
