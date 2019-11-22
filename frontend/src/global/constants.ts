export const OCIM_API_BASE =
  process.env.REACT_APP_OCIM_API_BASE || 'http://localhost:5000';

export const REACT_APP_CONTACT_US_LINK = process.env.REACT_APP_CONTACT_US_LINK || '/#';
export const REACT_APP_ENTERPRISE_COMPARISON_LINK = process.env.REACT_APP_ENTERPRISE_COMPARISON_LINK || '/#';

export enum RegistrationSteps {
  FIRST_STEP = 1,
  DOMAIN = 1,
  INSTANCE = 2,
  ACCOUNT = 3,
  THEME = 4,
  CONGRATS = 5,
  LAST_STEP = 5
}

export const ROUTES = {
  Registration: {
    HOME: '/registration',
    DOMAIN: '/registration/domain',
    INSTANCE: '/registration/instance',
    ACCOUNT: '/registration/account',
    THEME: '/registration/theme',
    CONGRATS: '/registration/congrats'
  }
};

export const REGISTRATION_STEPS = [
  ROUTES.Registration.DOMAIN,
  ROUTES.Registration.INSTANCE,
  ROUTES.Registration.ACCOUNT,
  ROUTES.Registration.THEME,
  ROUTES.Registration.CONGRATS
];
