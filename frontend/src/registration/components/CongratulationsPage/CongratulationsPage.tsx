import { RootState } from 'global/state';
import * as React from 'react';
import { connect } from 'react-redux';
import { NavLink } from 'react-router-dom';
import { Button } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import { RegistrationSteps, ROUTES } from 'global/constants';
import { RedirectToCorrectStep } from 'registration/components';
import { submitRegistration } from '../../actions';
import { RegistrationPage } from '../RegistrationPage';
import messages from './displayMessages';
import './styles.scss';

interface ActionProps {
  submitRegistration: Function;
}

interface Props extends ActionProps {
  currentRegistrationStep: RegistrationSteps;
}

interface State {}

@connect<{}, ActionProps, {}, Props, RootState>(
  (state: RootState) => ({
    ...state.registration
  }),
  {
    submitRegistration
  }
)
export class CongratulationsPage extends React.PureComponent<Props, State> {
  public render() {
    return (
      <RegistrationPage title="Pro & Teacher Account" currentStep={4}>
        <RedirectToCorrectStep
          currentPageStep={4}
          currentRegistrationStep={this.props.currentRegistrationStep}
        />
        <div className="congrats-page">
          <h1>
            <WrappedMessage messages={messages} id="congrats" />
          </h1>
          <p>
            <WrappedMessage messages={messages} id="congratsMessage" />
          </p>
          <p>
            <WrappedMessage
              messages={messages}
              id="congratsMessage2"
              values={{
                strong: (...chunks: string[]) => <strong>{chunks}</strong>
              }}
            />
          </p>
          <div className="text-center">
            <NavLink exact to={ROUTES.Console.HOME}>
              <Button size="lg">
                <WrappedMessage messages={messages} id="consoleButton" />
              </Button>
            </NavLink>
          </div>
        </div>
      </RegistrationPage>
    );
  }
}
