import { RootState } from 'global/state';
import * as React from 'react';
import { connect } from 'react-redux';
import { RegistrationNavButtons } from 'registration/components';
import { submitRegistration } from '../../actions';
import { getRegistrationData } from '../../selectors';
import { RegistrationPage } from '../RegistrationPage';
import './styles.scss';

interface ActionProps {
  submitRegistration: typeof submitRegistration;
}

interface StateProps {
  domain: string;
  domainIsExternal: boolean;
}

interface Props extends StateProps, ActionProps {}

@connect<StateProps, ActionProps, {}, Props, RootState>(
  (state: RootState) => ({
    domain: getRegistrationData(state, 'domain'),
    domainIsExternal: getRegistrationData(state, 'domainIsExternal')
  }),
  {
    submitRegistration
  }
)
export class AccountSetupPage extends React.PureComponent<Props> {
  render() {
    return (
      <RegistrationPage
        title="Create your Pro & Teacher Account"
        currentStep={3}
      >
        <div>Account page</div>
        <RegistrationNavButtons
          disableNextButton
          showBackButton
          showNextButton
          handleBackClick={() => {}}
          handleNextClick={() => {}}
        />
      </RegistrationPage>
    );
  }
}
