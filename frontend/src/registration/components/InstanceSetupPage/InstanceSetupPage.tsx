import { RootState } from 'global/state';
import * as React from 'react';
import { Form, FormControl, FormGroup, FormLabel } from 'react-bootstrap';
import { connect } from 'react-redux';
import { WrappedMessage } from 'utils/intl';
import { DomainSuccessJumbotron } from 'ui/components';
import { RegistrationNavButtons } from 'registration/components';
import { ROUTES } from 'global/constants';
import { submitInstanceInfo } from '../../actions';
import { getRegistrationData } from '../../selectors';
import { RegistrationPage } from '../RegistrationPage';
import messages from './displayMessages';
import './styles.scss';

interface ActionProps {
  submitInstanceInfo: typeof submitInstanceInfo;
}

interface StateProps {
  domain: string;
  domainIsExternal: boolean;
  instanceName: string;
  publicContactEmail: string;
}

interface Props extends StateProps, ActionProps {}

@connect<StateProps, ActionProps, {}, Props, RootState>(
  (state: RootState) => ({
    domain: getRegistrationData(state, 'domain'),
    domainIsExternal: getRegistrationData(state, 'domainIsExternal'),
    instanceName: getRegistrationData(state, 'instanceName'),
    publicContactEmail: getRegistrationData(state, 'publicContactEmail')
  }),
  {
    submitInstanceInfo
  }
)
export class InstanceSetupPage extends React.PureComponent<Props, StateProps> {
  public constructor(props: Props) {
    super(props);

    this.state = {
      domain: props.domain,
      domainIsExternal: props.domainIsExternal,
      instanceName: props.instanceName,
      publicContactEmail: props.publicContactEmail
    };
  }

  private onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const field = e.target.name;
    const { value } = e.target;

    this.setState<never>({ [field]: value });
  };

  private submitInstanceData = () => {
    this.props.submitInstanceInfo(
      {
        instanceName: this.state.instanceName,
        publicContactEmail: this.state.publicContactEmail
      },
      ROUTES.Registration.ACCOUNT
    );
  };

  render() {
    return (
      <RegistrationPage
        title="Create your Pro & Teacher Account"
        currentStep={2}
      >
        <DomainSuccessJumbotron
          domain={this.props.domain}
          domainIsExternal={this.props.domainIsExternal}
        />
        <Form className="secure-domain-form">
          <h2>
            <WrappedMessage id="secureYourDomain" messages={messages} />
          </h2>
          <FormGroup>
            <FormLabel>
              <WrappedMessage id="instanceName" messages={messages} />
            </FormLabel>
            <FormControl
              name="instanceName"
              value={this.state.instanceName}
              onChange={this.onChange}
            />
            <p>
              <WrappedMessage id="instanceNameHelp" messages={messages} />
            </p>
          </FormGroup>
          <FormGroup>
            <FormLabel>
              <WrappedMessage id="publicContactEmail" messages={messages} />
            </FormLabel>
            <FormControl
              type="email"
              name="publicContactEmail"
              value={this.state.publicContactEmail}
              onChange={this.onChange}
            />
            <p>
              <WrappedMessage id="publicContactEmailHelp" messages={messages} />
            </p>
          </FormGroup>
        </Form>
        <RegistrationNavButtons
          loading={false}
          disableNextButton={false}
          showBackButton
          showNextButton
          handleBackClick={() => {}}
          handleNextClick={this.submitInstanceData}
        />
      </RegistrationPage>
    );
  }
}
