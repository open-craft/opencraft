export const OCIM_API_BASE =
  process.env.REACT_APP_OCIM_API_BASE || 'http://localhost:5000';

export const CONTACT_US_LINK = process.env.REACT_APP_CONTACT_US_LINK || '/#';
export const ENTERPRISE_COMPARISON_LINK =
  process.env.REACT_APP_ENTERPRISE_COMPARISON_LINK || '/#';
export const TOS_LINK = process.env.REACT_APP_TOS_LINK || '/#';
export const PRIVACY_POLICY_LINK =
  process.env.REACT_APP_PRIVACY_POLICY_LINK || '/#';

export enum RegistrationSteps {
  FIRST_STEP = 1,
  DOMAIN = 1,
  INSTANCE = 2,
  ACCOUNT = 3,
  CONGRATS = 4,
  LAST_STEP = 4
}

export const ROUTES = {
  Registration: {
    HOME: '/registration',
    DOMAIN: '/registration/domain',
    INSTANCE: '/registration/instance',
    ACCOUNT: '/registration/account',
    CONGRATS: '/registration/congrats'
  }
};

export const REGISTRATION_STEPS = [
  ROUTES.Registration.DOMAIN,
  ROUTES.Registration.INSTANCE,
  ROUTES.Registration.ACCOUNT,
  ROUTES.Registration.CONGRATS
];
