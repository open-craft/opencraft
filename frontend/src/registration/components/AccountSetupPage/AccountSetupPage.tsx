import { RootState } from 'global/state';
import * as React from 'react';
import { connect } from 'react-redux';
import { Form } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import {
  RegistrationNavButtons,
  RedirectToCorrectStep
} from 'registration/components';
import { TextInputField } from 'ui/components';
import {
  RegistrationSteps,
  PRIVACY_POLICY_LINK,
  TOS_LINK
} from 'global/constants';
import { RegistrationStateModel } from 'registration/models';
import { clearErrorMessage, submitRegistration } from '../../actions';
import { RegistrationPage } from '../RegistrationPage';
import messages from './displayMessages';
import './styles.scss';

interface ActionProps {
  submitRegistration: Function;
  clearErrorMessage: Function;
}

interface State {
  [key: string]: string | boolean;
  fullName: string;
  username: string;
  email: string;
  password: string;
  passwordConfirm: string;
  acceptTOS: boolean;
  acceptPaidSupport: boolean;
  acceptDomainCondition: boolean;
  subscribeToUpdates: boolean;
}

interface StateProps extends RegistrationStateModel {}
interface Props extends StateProps, ActionProps {
  history: {
    goBack: Function;
  };
}

@connect<StateProps, ActionProps, {}, Props, RootState>(
  (state: RootState) => ({
    ...state.registration
  }),
  {
    submitRegistration,
    clearErrorMessage
  }
)
export class AccountSetupPage extends React.PureComponent<Props, State> {
  constructor(props: Props, state: State) {
    super(props);

    this.state = {
      fullName: this.props.registrationData.fullName,
      username: this.props.registrationData.username,
      email: this.props.registrationData.email,
      password: this.props.registrationData.password,
      passwordConfirm: this.props.registrationData.passwordConfirm,
      acceptTOS: this.props.registrationData.acceptTOS,
      acceptPaidSupport: this.props.registrationData.acceptPaidSupport,
      acceptDomainCondition: this.props.registrationData.acceptDomainCondition,
      subscribeToUpdates: this.props.registrationData.subscribeToUpdates
    };
  }

  private onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const field = e.target.name;
    let value: boolean | string;

    if (e.target.type === 'checkbox') {
      value = e.target.checked;
    } else {
      value = e.target.value;
    }

    this.setState({
      [field]: value
    });

    // Clear error message when the user changes field
    if (this.props.registrationFeedback[field]) {
      this.props.clearErrorMessage(field);
    }
  };

  private submitRegistration = () => {
    this.props.submitRegistration(
      {
        fullName: this.state.fullName,
        username: this.state.username,
        email: this.state.email,
        password: this.state.password,
        passwordConfirm: this.state.passwordConfirm,
        acceptTOS: this.state.acceptTOS,
        acceptPaidSupport: this.state.acceptPaidSupport,
        acceptDomainCondition: this.state.acceptDomainCondition,
        subscribeToUpdates: this.state.subscribeToUpdates
      },
      {
        externalDomain: this.props.registrationData.externalDomain,
        subdomain: this.props.registrationData.subdomain,
        instanceName: this.props.registrationData.instanceName
      },
      RegistrationSteps.CONGRATS
    );
  };

  render() {
    const checkboxLinks = {
      tos: (
        <a href={PRIVACY_POLICY_LINK} target="_blank" rel="noopener noreferrer">
          <WrappedMessage id="privacyPolicy" messages={messages} />
        </a>
      ),
      privacy_policy: (
        <a href={TOS_LINK} target="_blank" rel="noopener noreferrer">
          <WrappedMessage id="termsOfService" messages={messages} />
        </a>
      )
    };
    return (
      <RegistrationPage
        title="Create your Pro & Teacher Account"
        currentStep={3}
      >
        <RedirectToCorrectStep
          currentPageStep={3}
          currentRegistrationStep={this.props.currentRegistrationStep}
        />
        <Form className="account-form">
          <h2>
            <WrappedMessage id="createYourAccount" messages={messages} />
          </h2>
          <TextInputField
            fieldName="fullName"
            value={this.state.fullName}
            onChange={this.onChange}
            messages={messages}
            error={this.props.registrationFeedback.fullName}
          />
          <TextInputField
            fieldName="username"
            value={this.state.username}
            onChange={this.onChange}
            messages={messages}
            error={this.props.registrationFeedback.username}
          />
          <TextInputField
            fieldName="email"
            value={this.state.email}
            onChange={this.onChange}
            type="email"
            messages={messages}
            error={this.props.registrationFeedback.email}
          />
          <TextInputField
            fieldName="password"
            value={this.state.password}
            onChange={this.onChange}
            type="password"
            messages={messages}
            error={this.props.registrationFeedback.password}
          />
          <TextInputField
            fieldName="passwordConfirm"
            value={this.state.passwordConfirm}
            onChange={this.onChange}
            type="password"
            messages={messages}
            error={this.props.registrationFeedback.passwordConfirm}
          />
          <Form.Check type="checkbox" id="acceptTOS" custom>
            <Form.Check.Input
              type="checkbox"
              name="acceptTOS"
              checked={this.state.acceptTOS}
              onChange={this.onChange}
            />
            <Form.Check.Label>
              <WrappedMessage
                id="acceptTos"
                messages={messages}
                values={checkboxLinks}
              />
            </Form.Check.Label>
          </Form.Check>
          {this.props.registrationFeedback.acceptTOS && (
            <div className="invalid-feedback-checkbox">
              {this.props.registrationFeedback.acceptTOS}
            </div>
          )}
          <Form.Check type="checkbox" id="acceptPaidSupport" custom>
            <Form.Check.Input
              type="checkbox"
              name="acceptPaidSupport"
              checked={this.state.acceptPaidSupport}
              onChange={this.onChange}
            />
            <Form.Check.Label>
              <WrappedMessage id="acceptPaidSupport" messages={messages} />
            </Form.Check.Label>
          </Form.Check>
          {this.props.registrationFeedback.acceptPaidSupport && (
            <div className="invalid-feedback-checkbox">
              {this.props.registrationFeedback.acceptPaidSupport}
            </div>
          )}
          <Form.Check type="checkbox" id="acceptDomainCondition" custom>
            <Form.Check.Input
              type="checkbox"
              name="acceptDomainCondition"
              checked={this.state.acceptDomainCondition}
              onChange={this.onChange}
            />
            <Form.Check.Label>
              <WrappedMessage id="acceptDomainCondition" messages={messages} />
            </Form.Check.Label>
          </Form.Check>
          {this.props.registrationFeedback.acceptDomainCondition && (
            <div className="invalid-feedback-checkbox">
              {this.props.registrationFeedback.acceptDomainCondition}
            </div>
          )}
          <Form.Check type="checkbox" id="subscribeToUpdates" custom>
            <Form.Check.Input
              type="checkbox"
              name="subscribeToUpdates"
              checked={this.state.subscribeToUpdates}
              onChange={this.onChange}
            />
            <Form.Check.Label>
              <WrappedMessage id="subscribeToUpdates" messages={messages} />
            </Form.Check.Label>
          </Form.Check>
          {this.props.registrationFeedback.subscribeToUpdates && (
            <div className="invalid-feedback-checkbox">
              {this.props.registrationFeedback.subscribeToUpdates}
            </div>
          )}
        </Form>
        <RegistrationNavButtons
          loading={this.props.loading}
          disableNextButton={false}
          showBackButton
          showNextButton
          handleBackClick={() => {
            this.props.history.goBack();
          }}
          handleNextClick={this.submitRegistration}
        />
      </RegistrationPage>
    );
  }
}
