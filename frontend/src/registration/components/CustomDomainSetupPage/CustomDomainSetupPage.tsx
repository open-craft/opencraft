import { RegistrationSteps } from 'global/constants';
import { RootState } from 'global/state';
import * as React from 'react';
import { connect } from 'react-redux';
import { WrappedMessage } from 'utils/intl';
import { RedirectToCorrectStep } from 'registration/components';
import { RegistrationStateModel } from 'registration/models';
import { Row, Col, Button, Spinner } from 'react-bootstrap';
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
    const stepBox = (step: number, instruction: any, extra?: any) => {
      return (
        <div className="instruction-box">
          <Row>
            <Col lg="1" className="number">
              {step}
            </Col>
            <Col lg="11" className="instruction">
              {instruction}
            </Col>
          </Row>
          {extra && (
            <Row>
              <Col className="extra">{extra}</Col>
            </Row>
          )}
        </div>
      );
    };

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

            {stepBox(
              1,
              'If you already have a domain, skip this step. ' +
                "If you don't have a domain name yet, we recommend " +
                'you go to Gandi.net to order one. Come back to this page after ordering it.'
            )}
            {stepBox(
              2,
              'Go to your domain’s DNS configuration settings and add the following entries:',
              <table>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Value</th>
                </tr>
                <tr>
                  <td>{this.props.registrationData.externalDomain}</td>
                  <td>CNAME</td>
                  <td>haproxy.net.opencraft.hosting</td>
                </tr>
                <tr>
                  <td>
                    *.
                    {this.props.registrationData.externalDomain}
                  </td>
                  <td>CNAME</td>
                  <td>haproxy.net.opencraft.hosting</td>
                </tr>
              </table>
            )}
            {stepBox(
              3,
              'Save the changes and activate them if required. It might take a while for ' +
                'the domain changes to propagate (up to 6 hours).'
            )}

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
