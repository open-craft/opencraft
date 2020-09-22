import { RegistrationSteps } from 'global/constants';
import { RootState } from 'global/state';
import * as React from 'react';
import { connect } from 'react-redux';
import { WrappedMessage } from 'utils/intl';
import { DomainInput, InstitutionalAccountHero } from 'ui/components';
import { RedirectToCorrectStep } from 'registration/components';
import { RegistrationStateModel } from 'registration/models';
import { Nav } from 'react-bootstrap';
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
  externalDomain: string;
  domainIsExternal: boolean;
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
      subdomain: props.registrationData.subdomain,
      externalDomain: props.registrationData.externalDomain,
      domainIsExternal: false
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

  // private handleExternalDomainChange = (newDomain: string) => {
  //   this.setState({
  //     externalDomain: newDomain
  //   });
  //   // Clean up error feedback if any
  //   if (this.props.registrationFeedback.subdomain) {
  //     this.props.clearErrorMessage('externalDomain');
  //   }
  // };

  private submitDomain = () => {
    if (this.state.domainIsExternal) {
      this.props.performValidationAndStore(
        {
          externalDomain: this.state.externalDomain
        },
        RegistrationSteps.CUSTOM_DOMAIN
      );
    } else {
      this.props.performValidationAndStore(
        {
          subdomain: this.state.subdomain
        },
        RegistrationSteps.INSTANCE
      );
    }
  };

  private handleSwitchPageToExternal = (domainIsExternal: boolean) => {
    this.setState({ domainIsExternal });
  };

  private renderInternalDomain = () => {
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
            <Nav.Link
              onClick={() => {
                this.handleSwitchPageToExternal(true);
              }}
            >
              <WrappedMessage messages={messages} id="useOwnDomain" />
            </Nav.Link>
          </div>
        </RegistrationPage>
        <InstitutionalAccountHero />
      </div>
    );
  };

  // private renderExternalDomain = () => {
  //   return (
  //     <div className="div-fill">
  //       <RegistrationPage
  //         title="Pro & Teacher Account"
  //         subtitleBig="Register with your own domain"
  //         subtitle="Cost: +€25/month"
  //         currentStep={1}
  //       >
  //         <RedirectToCorrectStep
  //           currentPageStep={0}
  //           currentRegistrationStep={this.props.currentRegistrationStep}
  //         />
  //         <DomainInput
  //           domainName={this.state.externalDomain}
  //           error={this.props.registrationFeedback.externalDomain}
  //           internalDomain={false}
  //           loading={this.props.loading}
  //           handleDomainChange={this.handleExternalDomainChange}
  //           handleSubmitDomain={this.submitDomain}
  //         />
  //         <div className="use-own">
  //           <Nav.Link
  //             onClick={() => {
  //               this.handleSwitchPageToExternal(false);
  //             }}
  //           >
  //             <WrappedMessage messages={messages} id="useInternalDomain" />
  //           </Nav.Link>
  //         </div>
  //       </RegistrationPage>
  //       <InstitutionalAccountHero />
  //     </div>
  //   );
  // };

  public render() {
    // if (this.state.domainIsExternal) {
    //   return this.renderExternalDomain();
    // }

    return this.renderInternalDomain();
  }
}
