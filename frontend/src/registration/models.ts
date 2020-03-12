import { RegistrationSteps } from '../global/constants';

export enum Theme {
  LIGHT = 'light',
  DARK = 'dark'
}

export interface DomainInfoModel {
  subdomain: string;
  externalDomain: string;
}

export interface InstanceInfoModel {
  instanceName: string;
  publicContactEmail: string;
}

export interface AccountInfoModel {
  fullName: string;
  username: string;
  email: string;
  password: string;
  passwordConfirm: string;
  acceptTOS: boolean;
  acceptPaidSupport: boolean;
  subscribeToUpdates: boolean;
}

export interface ThemeInfoModel {
  mainColour: string;
  accentColour: string;
}

export const DefaultTheme: Readonly<ThemeInfoModel> = {
  mainColour: 'blue',
  accentColour: 'green'
};

export interface RegistrationModel
  extends DomainInfoModel,
    AccountInfoModel,
    InstanceInfoModel,
    ThemeInfoModel {}

export type RegistrationFields = keyof RegistrationModel;

export const blankRegistration: Readonly<RegistrationModel> = {
  acceptPaidSupport: false,
  acceptTOS: false,
  subscribeToUpdates: false,
  subdomain: '',
  externalDomain: '',
  email: '',
  fullName: '',
  instanceName: '',
  password: '',
  passwordConfirm: '',
  publicContactEmail: '',
  username: '',
  ...DefaultTheme
};

export interface DomainInfoValidationModel {
  [key: string]: string;
}

export interface RegistrationFeedbackModel extends DomainInfoValidationModel {}

export const blankRegistrationFeedbackModel: Readonly<RegistrationFeedbackModel> = {};

export interface RegistrationStateModel {
  currentRegistrationStep: RegistrationSteps;
  loading: boolean;
  registrationData: RegistrationModel;
  registrationFeedback: RegistrationFeedbackModel;
}

export const blankRegistrationState: Readonly<RegistrationStateModel> = {
  currentRegistrationStep: RegistrationSteps.FIRST_STEP,
  loading: false,
  registrationData: blankRegistration,
  registrationFeedback: blankRegistrationFeedbackModel
};
