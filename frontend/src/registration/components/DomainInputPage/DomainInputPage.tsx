import { ROUTES } from 'global/constants';
import { RootState } from 'global/state';
import * as React from 'react';
import { connect } from 'react-redux';
import { WrappedMessage } from 'utils/intl';
import { DomainInput, InstitutionalAccountHero } from 'ui/components';
import { performValidation, updateRootState } from '../../actions';
import { RegistrationPage } from '../RegistrationPage';
import messages from './displayMessages';
import './styles.scss';
import { RegistrationStateModel } from 'registration/models';

interface ActionProps {
  performValidation: Function;
  updateRootState: Function;
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
    performValidation,
    updateRootState
  }
)
export class DomainInputPage extends React.PureComponent<Props> {
  private handleDomainChange = (newDomain: string) => {
    this.props.updateRootState({
      registrationData: {
        domain: newDomain
      },
      registrationFeedback: {
        domain: ''
      }
    });
  };

  private submitDomain = () => {
    this.props.performValidation(
      { domain: this.props.registrationData.domain },
      ROUTES.Registration.INSTANCE
    );
  };

  public render() {
    console.log(this.props);
    return (
      <div className="div-fill">
        <RegistrationPage
          title="Pro & Teacher Account"
          subtitle="Create your own Open edX instance now."
          currentStep={1}
        >
          <DomainInput
            domainName={this.props.registrationData.domain}
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
