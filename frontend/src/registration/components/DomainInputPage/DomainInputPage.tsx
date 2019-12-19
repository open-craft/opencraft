import { RegistrationSteps } from 'global/constants';
import { RootState } from 'global/state';
import * as React from 'react';
import { connect } from 'react-redux';
import { WrappedMessage } from 'utils/intl';
import { DomainInput, InstitutionalAccountHero } from 'ui/components';
import { RedirectToCorrectStep } from 'registration/components';
import { RegistrationStateModel } from 'registration/models';
import { performValidationAndStore, clearErrorMessage } from '../../actions';
import { RegistrationPage } from '../RegistrationPage';
import messages from './displayMessages';
import './styles.scss';

interface ActionProps {
  performValidationAndStore: Function;
  clearErrorMessage: Function;
}

interface State {
  subdomain: string;
}

interface Props extends ActionProps {}
interface StateProps extends RegistrationStateModel {}

interface Props extends StateProps, ActionProps {}

@connect<{}, ActionProps, {}, Props, RootState>(
  (state: RootState) => ({
    ...state.registration
  }),
  {
    performValidationAndStore,
    clearErrorMessage
  }
)
export class DomainInputPage extends React.PureComponent<Props, State> {
  constructor(props: Props, state: State) {
    super(props);

    this.state = {
      subdomain: props.registrationData.subdomain
    };
  }

  private handleDomainChange = (newDomain: string) => {
    this.setState({
      subdomain: newDomain
    });
    // Clean up error feedback if any
    if (this.props.registrationFeedback.subdomain) {
      this.props.clearErrorMessage('subdomain');
    }
  };

  private submitDomain = () => {
    this.props.performValidationAndStore(
      {
        subdomain: this.state.subdomain
      },
      RegistrationSteps.INSTANCE
    );
  };

  public render() {
    return (
      <div className="div-fill">
        <RegistrationPage
          title="Pro & Teacher Account"
          subtitle="Create your own Open edX instance now."
          currentStep={1}
        >
          <RedirectToCorrectStep
            currentPageStep={0}
            currentRegistrationStep={this.props.currentRegistrationStep}
          />
          <DomainInput
            domainName={this.state.subdomain}
            error={this.props.registrationFeedback.subdomain}
            internalDomain
            loading={this.props.loading}
            handleDomainChange={this.handleDomainChange}
            handleSubmitDomain={this.submitDomain}
          />
          <div className="use-own">
            <a href="/#">
              <WrappedMessage messages={messages} id="useOwnDomain" />
            </a>
          </div>
        </RegistrationPage>
        <InstitutionalAccountHero />
      </div>
    );
  }
}
