import * as React from 'react';
import { RedeploymentToolbar } from 'console/components';
import { PreviewBox } from 'newConsole/components';
import { EmailActivationAlertMessage, ErrorPage } from 'ui/components';
import { OCIM_API_BASE } from 'global/constants';
import { Row, Col, Container, Button } from 'react-bootstrap';
import { InstancesModel } from 'console/models';
import { RootState } from 'global/state';
import { connect } from 'react-redux';
import {
  listUserInstances,
  getDeploymentStatus,
  performDeployment,
  cancelDeployment
} from 'console/actions';
import { WrappedMessage } from 'utils/intl';
import { ConsolePageCustomizationContainer } from 'newConsole/components';
import messages from './displayMessages';
import './styles.scss';

interface ActionProps {
  cancelDeployment: Function;
  getDeploymentStatus: Function;
  listUserInstances: Function;
  performDeployment: Function;
}

interface StateProps extends InstancesModel {}
interface Props extends StateProps, ActionProps {
  children: React.ReactNode;
  contentLoading: boolean;
  showSidebar: boolean;
  sideBarComponent: React.ReactNode;
  previewComponent: React.ReactNode;
  goBack: Function;
}

export class CustomizedConsolePageComponent extends React.PureComponent<Props> {
  refreshInterval?: NodeJS.Timer;

  // eslint-disable-next-line react/static-property-placement
  public static defaultProps: Partial<Props> = {
    showSidebar: true
  };

  public componentDidMount() {
    if (!this.props.loading && this.props.activeInstance.data === null) {
      this.props.listUserInstances();
    }

    this.refreshInterval = setInterval(() => {
      if (this.props.activeInstance.data) {
        this.props.getDeploymentStatus(this.props.activeInstance.data.id);
      }
    }, 5000);
  }

  componentWillUnmount() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
  }

  private performDeployment() {
    if (this.props.activeInstance.data) {
      this.props.performDeployment(this.props.activeInstance.data.id);
    }
  }

  private cancelDeployment() {
    if (this.props.activeInstance.data) {
      this.props.cancelDeployment(this.props.activeInstance.data.id);
    }
  }

  public render() {
    const content = () => {
      let innerContent = this.props.children;

      if (this.props.contentLoading) {
        innerContent = (
          <ConsolePageCustomizationContainer>
            <div className="loading">
              <i className="fas fa-2x fa-sync-alt fa-spin" />
            </div>
          </ConsolePageCustomizationContainer>
        );
      }

      if (this.props.showSidebar) {
        innerContent = (
          <Row className="justify-content-center-align">
            <Col md="3">
              <Button
                onClick={() => {
                  this.props.goBack();
                }}
                size="sm"
                variant="link"
                className="back-button"
              >
                <span>
                  <i className="fa fa-angle-left sm" aria-hidden="true" />
                </span>
                <span>
                  <WrappedMessage messages={messages} id="back" />
                </span>
              </Button>
              {this.props.children}
            </Col>
            <Col md="7">
              <PreviewBox>
                {/* This is where the preview page component will be redered*/}
                <div>The preview will render here</div>
              </PreviewBox>
            </Col>
          </Row>
        );
      }

      return innerContent;
    };
    if (
      this.props.error &&
      this.props.error.code === 'NOT_ACCESSIBLE_TO_STAFF'
    ) {
      return (
        <ErrorPage
          messages={messages}
          messageId="notAllowedForStaff"
          values={{
            link: (text: string) => (
              <a href={`${OCIM_API_BASE}/instance`}>{text}</a>
            )
          }}
        />
      );
    }

    let deploymentLoading = true;
    if (this.props.activeInstance && this.props.activeInstance.loading) {
      deploymentLoading = this.props.activeInstance.loading.includes(
        'deployment'
      );
    }

    let isEmailVerified = true;
    if (this.props.activeInstance && this.props.activeInstance.data) {
      isEmailVerified = this.props.activeInstance.data.isEmailVerified;
    }

    return (
      <div className="console-page">
        {!isEmailVerified ? (
          <EmailActivationAlertMessage />
        ) : (
          <RedeploymentToolbar
            deployment={
              this.props.activeInstance
                ? this.props.activeInstance.deployment
                : undefined
            }
            cancelRedeployment={() => {
              this.cancelDeployment();
            }}
            performDeployment={() => {
              this.performDeployment();
            }}
            loading={deploymentLoading}
          />
        )}

        <div className="new-console-page-container">
          <Row className="new-console-page-content">
            <Container fluid>{content()}</Container>
          </Row>
        </div>
      </div>
    );
  }
}

export const CustomizedConsolePage = connect<
  StateProps,
  ActionProps,
  {},
  Props,
  RootState
>((state: RootState) => state.console, {
  cancelDeployment,
  getDeploymentStatus,
  listUserInstances,
  performDeployment
})(CustomizedConsolePageComponent);
