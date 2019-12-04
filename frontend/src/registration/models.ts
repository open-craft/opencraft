export enum Theme {
  LIGHT = 'light',
  DARK = 'dark'
}

export interface DomainInfoModel {
  domain: string;
  domainIsExternal: boolean;
}

export interface DomainInfoValidationModel {
  domainError: string;
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

export interface RegistrationStateModel {
  loading: boolean;
}

export interface RegistrationModel
  extends DomainInfoModel,
    DomainInfoValidationModel,
    AccountInfoModel,
    InstanceInfoModel,
    ThemeInfoModel,
    RegistrationStateModel {}

export type RegistrationFields = keyof RegistrationModel;

export const blankRegistration: Readonly<RegistrationModel> = {
  acceptSupport: false,
  acceptTOS: false,
  acceptTipsEmail: false,
  cover: null,
  domain: '',
  domainError: '',
  domainIsExternal: false,
  emailAddress: '',
  fullName: '',
  instanceName: '',
  logo: null,
  password: '',
  passwordConfirm: '',
  publicContactEmail: '',
  username: '',
  loading: false,
  ...DefaultTheme
};
