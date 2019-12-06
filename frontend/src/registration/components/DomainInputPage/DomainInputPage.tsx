import { ROUTES } from 'global/constants';
import { RootState } from 'global/state';
import * as React from 'react';
import { connect } from 'react-redux';
import { WrappedMessage } from 'utils/intl';
import { DomainInput, InstitutionalAccountHero } from 'ui/components';
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
  domain: string;
}

interface Props extends ActionProps {}
interface StateProps extends RegistrationStateModel {}

interface Props extends StateProps, ActionProps {}

@connect<{}, ActionProps, {}, Props, RootState>(
  (state: RootState) => ({
    loading: state.registration.loading,
    registrationData: state.registration.registrationData,
    registrationFeedback: state.registration.registrationFeedback
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
      domain: props.registrationData.domain
    };
  }

  private handleDomainChange = (newDomain: string) => {
    this.setState({
      domain: newDomain
    });
    // Clean up error feedback if any
    if (this.props.registrationFeedback.domain) {
      this.props.clearErrorMessage({
        domain: ''
      });
    }
  };

  private submitDomain = () => {
    this.props.performValidationAndStore(
      {
        domain: this.state.domain
      },
      ROUTES.Registration.INSTANCE
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
          <DomainInput
            domainName={this.state.domain}
            error={this.props.registrationFeedback.domain}
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
