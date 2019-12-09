import { RootState } from 'global/state';
import * as React from 'react';
import { Form } from 'react-bootstrap';
import { connect } from 'react-redux';
import { WrappedMessage } from 'utils/intl';
import { DomainSuccessJumbotron, TextInputField } from 'ui/components';
import { RegistrationNavButtons } from 'registration/components';
import { ROUTES } from 'global/constants';
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
  [key: string]: string;
  instanceName: string;
  publicContactEmail: string;
}

interface StateProps extends RegistrationStateModel {}
interface Props extends StateProps, ActionProps {}

@connect<StateProps, ActionProps, {}, Props, RootState>(
  (state: RootState) => ({
    loading: state.registration.loading,
    registrationData: {
      ...state.registration.registrationData
    },
    registrationFeedback: {
      ...state.registration.registrationFeedback
    }
  }),
  {
    performValidationAndStore,
    clearErrorMessage
  }
)
export class InstanceSetupPage extends React.PureComponent<Props, State> {
  constructor(props: Props, state: State) {
    super(props);

    this.state = {
      instanceName: props.registrationData.instanceName,
      publicContactEmail: props.registrationData.publicContactEmail
    };
  }

  private onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const field = e.target.name;
    const { value } = e.target;

    this.setState({
      [field]: value
    });

    // Clear error message when the user changes field
    if (this.props.registrationFeedback[field]) {
      this.props.clearErrorMessage(field);
    }
  };

  private submitInstanceData = () => {
    this.props.performValidationAndStore(
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
          domain={this.props.registrationData.domain}
          domainIsExternal={this.props.registrationData.domainIsExternal}
        />
        <Form className="secure-domain-form">
          <h2>
            <WrappedMessage id="secureYourDomain" messages={messages} />
          </h2>

          <TextInputField
            fieldName="instanceName"
            value={this.state.instanceName}
            onChange={this.onChange}
            messages={messages}
            error={this.props.registrationFeedback.instanceName}
          />
          <TextInputField
            fieldName="publicContactEmail"
            value={this.state.publicContactEmail}
            onChange={this.onChange}
            messages={messages}
            type="email"
            error={this.props.registrationFeedback.publicContactEmail}
          />
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
