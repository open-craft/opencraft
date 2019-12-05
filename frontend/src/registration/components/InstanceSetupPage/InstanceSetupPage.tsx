import { RootState } from 'global/state';
import * as React from 'react';
import { Form, FormControl, FormGroup, FormLabel } from 'react-bootstrap';
import { connect } from 'react-redux';
import { WrappedMessage } from 'utils/intl';
import { DomainSuccessJumbotron } from 'ui/components';
import { RegistrationNavButtons } from 'registration/components';
import { ROUTES } from 'global/constants';
import { performValidation, updateRootState } from '../../actions';
import { RegistrationPage } from '../RegistrationPage';
import messages from './displayMessages';
import './styles.scss';
import { RegistrationStateModel } from 'registration/models'

interface ActionProps {
  performValidation: Function;
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
    performValidation,
    updateRootState
  }
)
export class InstanceSetupPage extends React.PureComponent<Props, StateProps> {
  private onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const field = e.target.name;
    const { value } = e.target;

    this.props.updateRootState({
      [field]: value
    });
  };

  private submitInstanceData = () => {
    this.props.performValidation({
        registrationData: {
          instanceName: this.props.registrationData.instanceName,
          publicContactEmail: this.props.registrationData.publicContactEmail
        }
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
          <FormGroup>
            <FormLabel>
              <WrappedMessage id="instanceName" messages={messages} />
            </FormLabel>
            <FormControl
              name="instanceName"
              value={this.props.registrationData.instanceName}
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
              value={this.props.registrationData.publicContactEmail}
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
