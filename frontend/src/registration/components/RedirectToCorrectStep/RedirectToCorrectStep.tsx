import * as React from 'react';
import { Redirect } from 'react-router';
import {
  ROUTES,
  REGISTRATION_STEPS,
  RegistrationSteps
} from 'global/constants';

interface Props {
  currentPageStep: RegistrationSteps;
  currentRegistrationStep: RegistrationSteps;
}

export const RedirectToCorrectStep: React.FC<Props> = (props: Props) => {
  if (props.currentRegistrationStep === RegistrationSteps.LAST_STEP) {
    return <Redirect to={ROUTES.Registration.CONGRATS} />;
  }
  if (props.currentPageStep > props.currentRegistrationStep) {
    const page = Math.min(
      props.currentRegistrationStep - 1,
      RegistrationSteps.FIRST_STEP
    );
    return <Redirect to={REGISTRATION_STEPS[page]} />;
  }
  return null;
};
