export const OCIM_API_BASE =
  process.env.REACT_APP_OCIM_API_BASE || 'http://localhost:5000';

export const CONTACT_US_LINK = process.env.REACT_APP_CONTACT_US_LINK || '/#';
export const ENTERPRISE_COMPARISON_LINK =
  process.env.REACT_APP_ENTERPRISE_COMPARISON_LINK || '/#';
export const TOS_LINK = process.env.REACT_APP_TOS_LINK || '/#';
export const PRIVACY_POLICY_LINK =
  process.env.REACT_APP_PRIVACY_POLICY_LINK || '/#';

export const INTERNAL_DOMAIN_NAME =
  process.env.REACT_APP_INTERNAL_DOMAIN_NAME || '.opencraft.hosting';

export enum RegistrationSteps {
  FIRST_STEP = 0,
  DOMAIN = 0,
  INSTANCE = 1,
  ACCOUNT = 2,
  CONGRATS = 3,
  LAST_STEP = 3
}

export const ROUTES = {
  Auth: {
    LOGIN: '/login',
    LOGOUT: '/logout',
  },
  Console: {
    HOME: '/console',
    INSTANCE_SETTINGS: '/console/instance_settings'
  },
  Registration: {
    HOME: '/registration',
    DOMAIN: '/registration/domain',
    INSTANCE: '/registration/instance',
    ACCOUNT: '/registration/account',
    CONGRATS: '/registration/congrats'
  },
  Error: {
    UNKNOWN_ERROR: '/error'
  }
};

export const REGISTRATION_STEPS = [
  ROUTES.Registration.DOMAIN,
  ROUTES.Registration.INSTANCE,
  ROUTES.Registration.ACCOUNT,
  ROUTES.Registration.CONGRATS
];
