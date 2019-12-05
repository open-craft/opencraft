import { ROUTES } from 'global/constants';
import { RootState } from 'global/state';
import * as React from 'react';
import { connect } from 'react-redux';
import { WrappedMessage } from 'utils/intl';
import { DomainInput, InstitutionalAccountHero } from 'ui/components';
import { submitRegistration, updateDomainInfoState } from '../../actions';
import { RegistrationPage } from '../RegistrationPage';
import { getRegistrationData } from '../../selectors';
import messages from './displayMessages';
import './styles.scss';

interface ActionProps {
  submitRegistration: Function;
  updateDomainInfoState: Function;
}

interface Props extends ActionProps {}

interface StateProps {
  domain: string;
  domainIsExternal: boolean;
  domainError: string;
  loading: boolean;
}

interface Props extends StateProps, ActionProps {}

@connect<{}, ActionProps, {}, Props, RootState>(
  (state: RootState) => ({
    domain: getRegistrationData(state, 'domain'),
    domainIsExternal: getRegistrationData(state, 'domainIsExternal'),
    domainError: getRegistrationData(state, 'domainError'),
    loading: getRegistrationData(state, 'loading')
  }),
  {
    submitRegistration,
    updateDomainInfoState
  }
)
export class DomainInputPage extends React.PureComponent<Props> {
  public constructor(props: Props) {
    super(props);
  }

  private handleDomainChange = (newDomain: string) => {
    this.props.updateDomainInfoState({
      domain: newDomain,
      domainError: ''
    });
  };

  private submitDomain = () => {
    this.props.submitRegistration(
      { domain: this.props.domain },
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
            domainName={this.props.domain}
            error={this.props.domainError}
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
