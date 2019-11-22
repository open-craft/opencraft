export enum Theme {
  LIGHT = 'light',
  DARK = 'dark'
}

export interface DomainInfoModel {
  domain: null | string;
}

export interface InstanceInfoModel {
  instanceName: null | string;
  publicEmail: null | string;
}

export interface AccountInfoModel {
  fullName: null | string;
  username: null | string;
  emailAddress: null | string;
  password: null | string;
  passwordConfirm: null | string;
  acceptTOS: null | boolean;
  acceptSupport: null | boolean;
  acceptTipsEmail: null | boolean;
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
  acceptSupport: null,
  acceptTOS: null,
  acceptTipsEmail: null,
  cover: null,
  domain: null,
  emailAddress: null,
  fullName: null,
  instanceName: null,
  logo: null,
  password: null,
  passwordConfirm: null,
  publicEmail: null,
  username: null,
  ...DefaultTheme
};
