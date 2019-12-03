import { ROUTES } from 'global/constants';
import { RootState } from 'global/state';
import * as React from 'react';
import { connect } from 'react-redux';
import { WrappedMessage } from 'utils/intl';
import { DomainInput, InstitutionalAccountHero } from 'ui/components';
import { submitRegistration } from '../../actions';
import { RegistrationPage } from '../RegistrationPage';
import messages from './displayMessages';
import './styles.scss';

interface ActionProps {
  submitRegistration: Function;
}

interface Props extends ActionProps {}

interface State {
  domainName: string;
}

@connect<{}, ActionProps, {}, Props, RootState>((state: RootState) => ({}), {
  submitRegistration
})
export class DomainInputPage extends React.PureComponent<Props, State> {
  public constructor(props: Props, state: State) {
    super(props);
    this.state = {
      domainName: ''
    };
  }

  private handleDomainChange = (newDomain: string) => {
    this.setState({
      domainName: newDomain || ''
    });
  };

  private submitDomain = () => {
    this.props.submitRegistration(
      { domain: this.state.domainName },
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
            domainName={this.state.domainName}
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
