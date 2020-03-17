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
  CUSTOM_DOMAIN = 1,
  INSTANCE = 2,
  ACCOUNT = 3,
  CONGRATS = 4,
  LAST_STEP = 4
}

export const ROUTES = {
  Auth: {
    LOGIN: '/login',
    LOGOUT: '/logout'
  },
  Console: {
    HOME: '/console',
    THEME_PREVIEW_AND_COLORS: '/console/theming/preview-and-colors',
    LOGOS: '/console/theming/logos',
    THEME_BUTTONS: '/console/theming/buttons',
    THEME_NAVIGATION: '/console/theming/navigation',
    INSTANCE_SETTINGS_GENERAL: '/console/settings/general'
  },
  Registration: {
    HOME: '/registration',
    DOMAIN: '/registration/domain',
    CUSTOM_DOMAIN: '/registration/custom-domain',
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
  ROUTES.Registration.CUSTOM_DOMAIN,
  ROUTES.Registration.INSTANCE,
  ROUTES.Registration.ACCOUNT,
  ROUTES.Registration.CONGRATS
];
