import { RootState } from 'global/state';
import * as React from 'react';
import { Form, FormControl, FormGroup, FormLabel } from 'react-bootstrap';
import { connect } from 'react-redux';
import { WrappedMessage } from 'utils/intl';
import { DomainSuccessJumbotron } from 'ui/components';
import { RegistrationNavButtons } from 'registration/components';
import { ROUTES } from 'global/constants';
import { validateInstanceInfo, updateInstanceInfoState } from '../../actions';
import { getRegistrationData } from '../../selectors';
import { RegistrationPage } from '../RegistrationPage';
import messages from './displayMessages';
import './styles.scss';

interface ActionProps {
  validateInstanceInfo: Function;
  updateInstanceInfoState: Function;
}

interface StateProps {
  domain: string;
  domainIsExternal: boolean;
  instanceName: string;
  publicContactEmail: string;
  loading: boolean;
}

interface Props extends StateProps, ActionProps {}

@connect<StateProps, ActionProps, {}, Props, RootState>(
  (state: RootState) => ({
    domain: getRegistrationData(state, 'domain'),
    domainIsExternal: getRegistrationData(state, 'domainIsExternal'),
    instanceName: getRegistrationData(state, 'instanceName'),
    publicContactEmail: getRegistrationData(state, 'publicContactEmail'),
    loading: getRegistrationData(state, 'loading')
  }),
  {
    validateInstanceInfo,
    updateInstanceInfoState
  }
)
export class InstanceSetupPage extends React.PureComponent<Props, StateProps> {
  public constructor(props: Props) {
    super(props);
  }

  private onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const field = e.target.name;
    const { value } = e.target;

    this.props.updateInstanceInfoState({
      [field]: value
    });
  };

  private submitInstanceData = () => {
    this.props.validateInstanceInfo(
      {
        instanceName: this.props.instanceName,
        publicContactEmail: this.props.publicContactEmail
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
              value={this.props.instanceName}
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
              value={this.props.publicContactEmail}
              onChange={this.onChange}
            />
            <p>
              <WrappedMessage id="publicContactEmailHelp" messages={messages} />
            </p>
          </FormGroup>
        </Form>
        <RegistrationNavButtons
          loading={this.props.loading}
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
