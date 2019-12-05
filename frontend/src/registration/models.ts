export enum Theme {
  LIGHT = 'light',
  DARK = 'dark'
}

export interface DomainInfoModel {
  domain: string;
  domainIsExternal: boolean;
}

export interface InstanceInfoModel {
  instanceName: string;
  publicContactEmail: string;
}

export interface AccountInfoModel {
  fullName: string;
  username: string;
  emailAddress: string;
  password: string;
  passwordConfirm: string;
  acceptTOS: boolean;
  acceptSupport: boolean;
  acceptTipsEmail: boolean;
}

export interface ThemeInfoModel {
  theme: Theme;
  mainColour: string;
  accentColour: string;
  logo: null | string;
  cover: null | string;
}

export const DefaultTheme: Readonly<ThemeInfoModel> = {
  theme: Theme.LIGHT,
  mainColour: 'blue',
  accentColour: 'green',
  logo: null,
  cover: null
};

export interface RegistrationModel
  extends DomainInfoModel,
    AccountInfoModel,
    InstanceInfoModel,
    ThemeInfoModel {}

export type RegistrationFields = keyof RegistrationModel;

export const blankRegistration: Readonly<RegistrationModel> = {
  acceptSupport: false,
  acceptTOS: false,
  acceptTipsEmail: false,
  cover: null,
  domain: '',
  domainIsExternal: false,
  emailAddress: '',
  fullName: '',
  instanceName: '',
  logo: null,
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
  loading: boolean;
  registrationData: RegistrationModel;
  registrationFeedback: RegistrationFeedbackModel;
}

export const blankRegistrationState: Readonly<RegistrationStateModel> = {
  loading: false,
  registrationData: blankRegistration,
  registrationFeedback: blankRegistrationFeedbackModel
};
