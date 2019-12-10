import { RootState } from 'global/state';
import * as React from 'react';
import { connect } from 'react-redux';
import { WrappedMessage } from 'utils/intl';
import { submitRegistration } from '../../actions';
import { RegistrationPage } from '../RegistrationPage';
import messages from './displayMessages';
import './styles.scss';

interface ActionProps {
  submitRegistration: Function;
}

interface Props extends ActionProps {}

interface State {}

@connect<{}, ActionProps, {}, Props, RootState>((state: RootState) => ({}), {
  submitRegistration
})
export class CongratulationsPage extends React.PureComponent<Props, State> {
  public constructor(props: Props, state: State) {
    super(props);
  }

  public render() {
    return (
      <RegistrationPage title="Pro & Teacher Account" currentStep={4}>
        <div className="congrats-page">
          <h1>
            <WrappedMessage messages={messages} id="congrats" />
          </h1>
          <p>
            <WrappedMessage messages={messages} id="congratsMessage" />
          </p>
          <p>
            <WrappedMessage messages={messages} id="congratsMessage2" />
          </p>
        </div>
      </RegistrationPage>
    );
  }
}
