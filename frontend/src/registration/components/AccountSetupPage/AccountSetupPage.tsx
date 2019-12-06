import { RootState } from 'global/state';
import * as React from 'react';
import { connect } from 'react-redux';
import { Form } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import { RegistrationNavButtons } from 'registration/components';
import { TextInputField } from 'ui/components';
import { PRIVACY_POLICY_LINK, ROUTES, TOS_LINK } from 'global/constants';
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
  emailAddress: string;
  password: string;
  passwordConfirm: string;
  acceptTOS: boolean;
  acceptSupport: boolean;
  acceptTipsEmail: boolean;
}

interface StateProps extends RegistrationStateModel {}
interface Props extends StateProps, ActionProps {}

@connect<StateProps, ActionProps, {}, Props, RootState>(
  (state: RootState) => ({
    loading: state.registration.loading,
    registrationData: state.registration.registrationData,
    registrationFeedback: state.registration.registrationFeedback
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
      emailAddress: this.props.registrationData.emailAddress,
      password: this.props.registrationData.password,
      passwordConfirm: this.props.registrationData.passwordConfirm,
      acceptTOS: this.props.registrationData.acceptTOS,
      acceptSupport: this.props.registrationData.acceptSupport,
      acceptTipsEmail: this.props.registrationData.acceptTipsEmail
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
      this.props.clearErrorMessage({
        [field]: ''
      });
    }
  };

  private submitRegistration = () => {
    this.props.submitRegistration(
      {
        fullName: this.state.fullName,
        username: this.state.username,
        emailAddress: this.state.emailAddress,
        password: this.state.password,
        passwordConfirm: this.state.passwordConfirm,
        acceptTOS: this.state.acceptTOS,
        acceptSupport: this.state.acceptSupport,
        acceptTipsEmail: this.state.acceptTipsEmail
      },
      ROUTES.Registration.CONGRATS
    );
  };

  render() {
    const checkboxLinks = {
      tos: (
        <a href={PRIVACY_POLICY_LINK}>
          <WrappedMessage id="privacyPolicy" messages={messages} />
        </a>
      ),
      privacy_policy: (
        <a href={TOS_LINK}>
          <WrappedMessage id="termsOfService" messages={messages} />
        </a>
      )
    };
    return (
      <RegistrationPage
        title="Create your Pro & Teacher Account"
        currentStep={3}
      >
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
            fieldName="emailAddress"
            value={this.state.emailAddress}
            onChange={this.onChange}
            type="email"
            messages={messages}
            error={this.props.registrationFeedback.emailAddress}
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
          <Form.Check type="checkbox" id="acceptSupport" custom>
            <Form.Check.Input
              type="checkbox"
              name="acceptSupport"
              checked={this.state.acceptSupport}
              onChange={this.onChange}
            />
            <Form.Check.Label>
              <WrappedMessage id="acceptSupport" messages={messages} />
            </Form.Check.Label>
          </Form.Check>
          {this.props.registrationFeedback.acceptSupport && (
            <div className="invalid-feedback-checkbox">
              {this.props.registrationFeedback.acceptSupport}
            </div>
          )}
          <Form.Check type="checkbox" id="acceptTipsEmail" custom>
            <Form.Check.Input
              type="checkbox"
              name="acceptTipsEmail"
              checked={this.state.acceptTipsEmail}
              onChange={this.onChange}
            />
            <Form.Check.Label>
              <WrappedMessage id="acceptTipsEmail" messages={messages} />
            </Form.Check.Label>
          </Form.Check>
          {this.props.registrationFeedback.acceptTipsEmail && (
            <div className="invalid-feedback-checkbox">
              {this.props.registrationFeedback.acceptTipsEmail}
            </div>
          )}
        </Form>
        <RegistrationNavButtons
          loading={this.props.loading}
          disableNextButton={false}
          showBackButton
          showNextButton
          handleBackClick={() => {}}
          handleNextClick={this.submitRegistration}
        />
      </RegistrationPage>
    );
  }
}
