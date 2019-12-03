import { ROUTES } from 'global/constants';
import { RootState } from 'global/state';
import * as React from 'react';
import { connect } from 'react-redux';
import { WrappedMessage } from 'utils/intl';
import { DomainInput, InstitutionalAccountHero } from 'ui/components';
import { submitRegistration } from '../../actions';
import { RegistrationPage } from '../RegistrationPage';
import { getRegistrationData } from '../../selectors';
import messages from './displayMessages';
import './styles.scss';

interface ActionProps {
  submitRegistration: Function;
}

interface Props extends ActionProps {}

interface StateProps {
  domain: string;
}

interface Props extends StateProps, ActionProps {}

@connect<{}, ActionProps, {}, Props, RootState>(
  (state: RootState) => ({
    domain: getRegistrationData(state, 'domain'),
    domainIsExternal: getRegistrationData(state, 'domainIsExternal')
  }),
  {
    submitRegistration
  }
)
export class DomainInputPage extends React.PureComponent<Props, StateProps> {
  public constructor(props: Props, state: StateProps) {
    super(props);
    this.state = {
      domain: props.domain
    };
  }

  private handleDomainChange = (newDomain: string) => {
    this.setState({
      domain: newDomain || ''
    });
  };

  private submitDomain = () => {
    this.props.submitRegistration(
      { domain: this.state.domain },
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
            internalDomain
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
