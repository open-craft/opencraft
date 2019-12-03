import { RootState } from 'global/state';
import * as React from 'react';
import { connect } from 'react-redux';
import { Form, FormControl, FormGroup, FormLabel } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import { RegistrationNavButtons } from 'registration/components';
import { PRIVACY_POLICY_LINK, TOS_LINK } from 'global/constants';
import { submitRegistration } from '../../actions';
import { getRegistrationData } from '../../selectors';
import { RegistrationPage } from '../RegistrationPage';
import messages from './displayMessages';
import './styles.scss';

interface ActionProps {
  submitRegistration: typeof submitRegistration;
}

interface StateProps {
  domain: string;
  domainIsExternal: boolean;
}

interface Props extends StateProps, ActionProps {}

@connect<StateProps, ActionProps, {}, Props, RootState>(
  (state: RootState) => ({
    domain: getRegistrationData(state, 'domain'),
    domainIsExternal: getRegistrationData(state, 'domainIsExternal')
  }),
  {
    submitRegistration
  }
)
export class AccountSetupPage extends React.PureComponent<Props> {
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
          <FormGroup>
            <FormLabel>
              <WrappedMessage id="fullName" messages={messages} />
            </FormLabel>
            <FormControl />
            <p>
              <WrappedMessage id="fullNameHelp" messages={messages} />
            </p>
          </FormGroup>
          <FormGroup>
            <FormLabel>
              <WrappedMessage id="username" messages={messages} />
            </FormLabel>
            <FormControl />
            <p>
              <WrappedMessage id="usernameHelp" messages={messages} />
            </p>
          </FormGroup>
          <FormGroup>
            <FormLabel>
              <WrappedMessage id="email" messages={messages} />
            </FormLabel>
            <FormControl type="email" />
            <p>
              <WrappedMessage id="emailHelp" messages={messages} />
            </p>
          </FormGroup>
          <FormGroup>
            <FormLabel>
              <WrappedMessage id="password" messages={messages} />
            </FormLabel>
            <FormControl type="password" />
            <p>
              <WrappedMessage id="passwordHelp" messages={messages} />
            </p>
          </FormGroup>
          <FormGroup>
            <FormLabel>
              <WrappedMessage id="confirmPassword" messages={messages} />
            </FormLabel>
            <FormControl type="password" />
            <p>
              <WrappedMessage id="confirmPasswordHelp" messages={messages} />
            </p>
          </FormGroup>
          <Form.Check type="checkbox" id="acceptTos" custom>
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
          <Form.Check type="checkbox" id="acceptNewsletter" custom>
            <Form.Check.Input type="checkbox" />
            <Form.Check.Label>
              <WrappedMessage id="acceptNewsletter" messages={messages} />
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
