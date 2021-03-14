export const NOTIFICATIONS_LIMIT = process.env.REACT_APP_NOTIFICATIONS_LIMIT
  ? Number(process.env.REACT_APP_NOTIFICATIONS_LIMIT)
  : 6;

export const OCIM_API_BASE =
  process.env.REACT_APP_OCIM_API_BASE || 'http://localhost:5000';

export const SUPPORT_LINK = process.env.REACT_APP_SUPPORT_LINK || '/#';
export const CONTACT_US_LINK = process.env.REACT_APP_CONTACT_US_LINK || '/#';
export const CONTACT_US_EMAIL =
  process.env.REACT_APP_CONTACT_US_EMAIL || 'contact@opencraft.com';
export const ENTERPRISE_COMPARISON_LINK =
  process.env.REACT_APP_ENTERPRISE_COMPARISON_LINK || '/#';
export const TOS_LINK = process.env.REACT_APP_TOS_LINK || '/#';
export const PRIVACY_POLICY_LINK =
  process.env.REACT_APP_PRIVACY_POLICY_LINK || '/#';
export const FAQ_PAGE_LINK = process.env.REACT_APP_FAQ_PAGE_LINK || '/#';
export const OPENCRAFT_WEBSITE_LINK =
  process.env.REACT_APP_OPENCRAFT_WEBSITE_LINK || 'https://opencraft.com';

export const INTERNAL_DOMAIN_NAME =
  process.env.REACT_APP_INTERNAL_DOMAIN_NAME || '.opencraft.hosting';

export const GANDI_REFERRAL_LINK =
  process.env.REACT_APP_GANDI_REFERRAL_LINK || 'https://gandi.link/';

export const MATOMO_BASE_URL = process.env.REACT_APP_MATOMO_BASE_URL || '';

export const MATOMO_SITE_ID = process.env.REACT_APP_MATOMO_SITE_ID || '1';

export const MATOMO_MY_DOMAIN = process.env.REACT_APP_MATOMO_MY_DOMAIN || '';

export const MATOMO_ALIAS_DOMAIN =
  process.env.REACT_APP_MATOMO_ALIAS_DOMAIN || '';

export interface StringIndexedArray {
  [key: string]: any;
}

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
    EMAIL_VERIFICATION: '/verify-email/:verificationCode',
    LOGIN: '/login',
    LOGOUT: '/logout',
    PASSWORD_FORGOTTEN: '/password-forgotten',
    PASSWORD_RESET: '/password-reset/:token'
  },
  Console: {
    HOME: '/console',
    NOTICE_BOARD: '/console/notice',
    CUSTOM_PAGES: '/console/custom-pages/:pageName',
    THEME_PREVIEW_AND_COLORS: '/console/theming/preview-and-colors',
    LOGOS: '/console/theming/logos',
    THEME_BUTTONS: '/console/theming/buttons',
    THEME_NAVIGATION: '/console/theming/navigation',
    THEME_FOOTER: '/console/theming/footer',
    INSTANCE_SETTINGS_GENERAL: '/console/settings/general',
    HERO: '/console/theming/hero',
    NEW_HOME: '/newconsole',
    NEW_LOGOS: '/newconsole/theming/logos',
    COURSES: '/console/courses/manage'
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
  },
  Demo: {
    COMPONENTS_DEMO: '/demo'
  }
};

export const REGISTRATION_STEPS = [
  ROUTES.Registration.DOMAIN,
  ROUTES.Registration.CUSTOM_DOMAIN,
  ROUTES.Registration.INSTANCE,
  ROUTES.Registration.ACCOUNT,
  ROUTES.Registration.CONGRATS
];

export const AVAILABLE_CUSTOM_PAGES = [
  'about',
  'contact',
  'donate',
  'tos',
  'honor',
  'privacy'
];

export const LMS_CUSTOM_PAGE_LINK_MAP: StringIndexedArray = {
  about: 'about',
  contact: 'contact',
  donate: 'donate',
  tos: 'tos',
  honor: 'honor',
  privacy: 'privacy'
};
