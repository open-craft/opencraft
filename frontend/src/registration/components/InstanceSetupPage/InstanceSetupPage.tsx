import { RootState } from 'global/state';
import * as React from 'react';
import { Form, FormControl, FormGroup, FormLabel } from 'react-bootstrap';
import { connect } from 'react-redux';
import { WrappedMessage } from 'utils/intl';
import { DomainSuccessJumbotron } from 'ui/components/DomainSuccessJumbotron';
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
export class InstanceSetupPage extends React.PureComponent<Props> {
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
        <Form>
          <h2>
            <WrappedMessage id="secureYourDomain" messages={messages} />
          </h2>
          <FormGroup>
            <FormLabel>
              <WrappedMessage id="instanceName" messages={messages} />
            </FormLabel>
            <FormControl />
            <p>
              <WrappedMessage id="instanceNameHelp" messages={messages} />
            </p>
          </FormGroup>
          <FormGroup>
            <FormLabel>
              <WrappedMessage id="publicContactEmail" messages={messages} />
            </FormLabel>
            <FormControl type="email" />
            <p>
              <WrappedMessage id="publicContactEmailHelp" messages={messages} />
            </p>
          </FormGroup>
        </Form>
      </RegistrationPage>
    );
  }
}
