import { RootState } from 'global/state';
import * as React from 'react';
import { connect } from 'react-redux';
import { Form, FormControl, FormGroup, FormLabel } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import { RegistrationNavButtons } from 'registration/components';
import { PRIVACY_POLICY_LINK, TOS_LINK } from 'global/constants';
import { submitRegistration } from '../../actions';
import { getRegistrationData } from '../../selectors';
import { AccountInfoModel } from '../../models';
import { RegistrationPage } from '../RegistrationPage';
import messages from './displayMessages';
import './styles.scss';

interface ActionProps {
  submitRegistration: typeof submitRegistration;
}

interface Props extends AccountInfoModel, ActionProps {}

interface InputFieldProps {
  fieldName: string;
  value: string;
  onChange: any;
  type?: string;
}

const InputField: React.SFC<InputFieldProps> = (props: InputFieldProps) => {
  return (
    <FormGroup>
      <FormLabel>
        <WrappedMessage id={props.fieldName} messages={messages} />
      </FormLabel>
      <FormControl
        name={props.fieldName}
        value={props.value}
        onChange={props.onChange}
        type={props.type}
      />
      <p>
        <WrappedMessage id={`${props.fieldName}Help`} messages={messages} />
      </p>
    </FormGroup>
  );
};

@connect<AccountInfoModel, ActionProps, {}, Props, RootState>(
  (state: RootState) => ({
    fullName: getRegistrationData(state, 'fullName'),
    username: getRegistrationData(state, 'username'),
    emailAddress: getRegistrationData(state, 'emailAddress'),
    password: getRegistrationData(state, 'password'),
    passwordConfirm: getRegistrationData(state, 'passwordConfirm'),
    acceptTOS: getRegistrationData(state, 'acceptTOS'),
    acceptSupport: getRegistrationData(state, 'acceptSupport'),
    acceptTipsEmail: getRegistrationData(state, 'acceptTipsEmail')
  }),
  {
    submitRegistration
  }
)
export class AccountSetupPage extends React.PureComponent<
  Props,
  AccountInfoModel
> {
  public constructor(props: Props, state: AccountInfoModel) {
    super(props);

    this.state = {
      fullName: props.fullName,
      username: props.username,
      emailAddress: props.emailAddress,
      password: props.password,
      passwordConfirm: props.passwordConfirm,
      acceptTOS: props.acceptTOS,
      acceptSupport: props.acceptSupport,
      acceptTipsEmail: props.acceptTipsEmail
    };
  }

  private onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const field = e.target.name;
    const { value } = e.target;
    this.setState<never>({ [field]: value });
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
          <InputField
            fieldName="fullName"
            value={this.state.fullName}
            onChange={this.onChange}
          />
          <InputField
            fieldName="username"
            value={this.state.username}
            onChange={this.onChange}
          />
          <InputField
            fieldName="emailAddress"
            value={this.state.emailAddress}
            onChange={this.onChange}
            type="email"
          />
          <InputField
            fieldName="password"
            value={this.state.password}
            onChange={this.onChange}
            type="password"
          />
          <InputField
            fieldName="passwordConfirm"
            value={this.state.passwordConfirm}
            onChange={this.onChange}
            type="password"
          />
          <Form.Check type="checkbox" id="acceptTOS" custom>
            <Form.Check.Input type="checkbox" />
            <Form.Check.Label>
              <WrappedMessage
                id="acceptTos"
                messages={messages}
                values={checkboxLinks}
              />
            </Form.Check.Label>
          </Form.Check>
          <Form.Check type="checkbox" id="acceptSupport" custom>
            <Form.Check.Input type="checkbox" />
            <Form.Check.Label>
              <WrappedMessage id="acceptSupport" messages={messages} />
            </Form.Check.Label>
          </Form.Check>
          <Form.Check
            type="checkbox"
            id="acceptTipsEmail"
            custom
          >
            <Form.Check.Input type="checkbox" />
            <Form.Check.Label>
              <WrappedMessage id="acceptTipsEmail" messages={messages} />
            </Form.Check.Label>
          </Form.Check>
        </Form>
        <RegistrationNavButtons
          loading={false}
          disableNextButton
          showBackButton
          showNextButton
          handleBackClick={() => {}}
          handleNextClick={() => {}}
        />
      </RegistrationPage>
    );
  }
}
