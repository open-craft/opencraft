import { GANDI_REFERRAL_LINK, RegistrationSteps } from 'global/constants';
import { RootState } from 'global/state';
import * as React from 'react';
import { connect } from 'react-redux';
import { WrappedMessage } from 'utils/intl';
import { RedirectToCorrectStep } from 'registration/components';
import { RegistrationStateModel } from 'registration/models';
import { Button, Col, Row, Spinner } from 'react-bootstrap';
import { goToNextStep } from '../../actions';
import { RegistrationPage } from '../RegistrationPage';
import messages from './displayMessages';
import './styles.scss';

interface ActionProps {
  goToNextStep: Function;
}

interface State {
  externalDomain: string;
}

interface Props extends ActionProps {}
interface StateProps extends RegistrationStateModel {}

interface Props extends StateProps, ActionProps {}

interface StepBoxProps {
  step: number;
  instruction: any;
  extra?: any;
}
export const StepBox: React.SFC<StepBoxProps> = (props: StepBoxProps) => (
  <div className="instruction-box">
    <Row>
      <Col lg="1" className="number">
        {props.step}
      </Col>
      <Col lg="11" className="instruction">
        {props.instruction}
      </Col>
    </Row>
    {props.extra && (
      <Row>
        <Col className="extra">{props.extra}</Col>
      </Row>
    )}
  </div>
);

@connect<{}, ActionProps, {}, Props, RootState>(
  (state: RootState) => ({
    ...state.registration
  }),
  {
    goToNextStep
  }
)
export class CustomDomainSetupPage extends React.PureComponent<Props, State> {
  constructor(props: Props, state: State) {
    super(props);
  }

  public render() {
    const setDnsRecordsStepExtraContent = (
      <table>
        <tr>
          <th>Name</th>
          <th>Type</th>
          <th>Value</th>
        </tr>
        <tr>
          <td>{this.props.registrationData.externalDomain}</td>
          <td>CNAME</td>
          <td>haproxy.net.opencraft.hosting.</td>
        </tr>
        <tr>
          <td>
            *.
            {this.props.registrationData.externalDomain}
          </td>
          <td>CNAME</td>
          <td>haproxy.net.opencraft.hosting.</td>
        </tr>
      </table>
    );

    const buyDomainInstruction = (
      <WrappedMessage
        messages={messages}
        id="buyDomainStep"
        values={{
          a: (...chunks: string[]) => (
            <a
              href={GANDI_REFERRAL_LINK}
              target="_blank"
              rel="noopener noreferrer"
            >
              {chunks}
            </a>
          )
        }}
      />
    );

    return (
      <div className="div-fill">
        <RegistrationPage
          title="Pro & Teacher Account"
          subtitle="Create your own Open edX instance now."
          currentStep={1}
        >
          <RedirectToCorrectStep
            currentPageStep={1}
            currentRegistrationStep={this.props.currentRegistrationStep}
          />
          <div className="custom-domain-setup">
            <h1>
              <WrappedMessage messages={messages} id="configureOwnDomain" />
            </h1>

            <p>
              <WrappedMessage
                messages={messages}
                id="configureOwnDomainInstructions"
              />
            </p>

            <StepBox step={1} instruction={buyDomainInstruction} />
            <StepBox
              step={2}
              instruction={
                <WrappedMessage messages={messages} id="setDnsRecordsStep" />
              }
              extra={setDnsRecordsStepExtraContent}
            />
            <StepBox
              step={3}
              instruction={<WrappedMessage messages={messages} id="saveStep" />}
            />

            <Button
              className="pull-left loading"
              variant="primary"
              size="lg"
              disabled={this.props.loading}
              onClick={() => {
                this.props.goToNextStep(RegistrationSteps.INSTANCE);
              }}
            >
              {this.props.loading && (
                <Spinner animation="border" size="sm" className="spinner" />
              )}
              <WrappedMessage messages={messages} id="changesMade" />
            </Button>
          </div>
        </RegistrationPage>
      </div>
    );
  }
}
