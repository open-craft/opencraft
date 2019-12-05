import { RootState } from 'global/state';
import * as React from 'react';
import { connect } from 'react-redux';
import { Form } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import { RegistrationNavButtons } from 'registration/components';
import { TextInputField } from 'ui/components';
import { PRIVACY_POLICY_LINK, ROUTES, TOS_LINK } from 'global/constants';
import { RegistrationStateModel } from 'registration/models';
import { updateRootState, submitRegistration } from '../../actions';
import { RegistrationPage } from '../RegistrationPage';
import messages from './displayMessages';
import './styles.scss';

interface ActionProps {
  submitRegistration: Function;
  updateRootState: Function;
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
    updateRootState
  }
)
export class AccountSetupPage extends React.PureComponent<Props> {
  private onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const field = e.target.name;
    const { value } = e.target;

    this.props.updateRootState({
      registrationData: {
        [field]: value
      },
      registrationFeedback: {
        [field]: ''
      }
    });
  };

  private submitRegistration = () => {
    this.props.submitRegistration({}, ROUTES.Registration.CONGRATS);
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
            value={this.props.registrationData.fullName}
            onChange={this.onChange}
            messages={messages}
          />
          <TextInputField
            fieldName="username"
            value={this.props.registrationData.username}
            onChange={this.onChange}
            messages={messages}
          />
          <TextInputField
            fieldName="emailAddress"
            value={this.props.registrationData.emailAddress}
            onChange={this.onChange}
            type="email"
            messages={messages}
          />
          <TextInputField
            fieldName="password"
            value={this.props.registrationData.password}
            onChange={this.onChange}
            type="password"
            messages={messages}
          />
          <TextInputField
            fieldName="passwordConfirm"
            value={this.props.registrationData.passwordConfirm}
            onChange={this.onChange}
            type="password"
            messages={messages}
          />
          <Form.Check type="checkbox" id="acceptTOS" custom>
            <Form.Check.Input
              type="checkbox"
              name="acceptTOS"
              checked={this.props.registrationData.acceptTOS}
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
          <Form.Check type="checkbox" id="acceptSupport" custom>
            <Form.Check.Input
              type="checkbox"
              name="acceptSupport"
              checked={this.props.registrationData.acceptSupport}
              onChange={this.onChange}
            />
            <Form.Check.Label>
              <WrappedMessage id="acceptSupport" messages={messages} />
            </Form.Check.Label>
          </Form.Check>
          <Form.Check type="checkbox" id="acceptTipsEmail" custom>
            <Form.Check.Input
              type="checkbox"
              name="acceptTipsEmail"
              checked={this.props.registrationData.acceptTipsEmail}
              onChange={this.onChange}
            />
            <Form.Check.Label>
              <WrappedMessage id="acceptTipsEmail" messages={messages} />
            </Form.Check.Label>
          </Form.Check>
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
