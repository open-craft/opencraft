import * as React from 'react';
import { RedeploymentToolbar, CustomizationSideMenu } from 'console/components';
import { Row, Col, Container } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import { InstancesModel } from 'console/models';
import { RootState } from 'global/state';
import { connect } from 'react-redux';
import {
  listUserInstances,
  getDeploymentStatus,
  performDeployment,
  cancelDeployment
} from 'console/actions';
import messages from './displayMessages';
import './styles.scss';
import { AlertMessage } from '../AlertMessage/AlertMessage';

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
}

interface CustomizationContainerProps {
  children: React.ReactNode;
}

export const ConsolePageCustomizationContainer: React.FC<CustomizationContainerProps> = (
  props: CustomizationContainerProps
) => <div className="customization-form">{props.children}</div>;

export class ConsolePageComponent extends React.PureComponent<Props> {
  refreshInterval?: NodeJS.Timer;

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

  private renderHeader() {
    if (this.props.loading || this.props.activeInstance.data === null) {
      return (
        <div className="title-container">
          <h1>
            <i className="fas fa-sync-alt fa-spin" />
          </h1>
        </div>
      );
    }

    const instanceData = this.props.activeInstance.data;
    const instanceLink = instanceData.lmsUrl;
    const studioLink = instanceData.studioUrl;

    return (
      <div className="title-container">
        <h1>
          <a className="header-link" href={instanceLink}>
            {instanceData.instanceName}
            <i className="instance-link fas fa-link fa-xs" />
          </a>
        </h1>
        <h2>
          <a className="header-link" href={studioLink}>
            <WrappedMessage messages={messages} id="editCourses" />
          </a>
        </h2>
      </div>
    );
  }

  public render() {
    const content = () => {
      if (this.props.contentLoading) {
        return (
          <ConsolePageCustomizationContainer>
            <div className="loading">
              <i className="fas fa-2x fa-sync-alt fa-spin" />
            </div>
          </ConsolePageCustomizationContainer>
        );
      }
      return this.props.children;
    };

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
        {this.renderHeader()}

        {!isEmailVerified ? (
          <AlertMessage>
            <WrappedMessage id="verifyEmail" messages={messages} />
          </AlertMessage>
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

        <div className="console-page-container">
          <Row className="console-page-content">
            <Container fluid>
              <Row>
                <Col md="3">
                  <CustomizationSideMenu />
                </Col>
                <Col md="9">{content()}</Col>
              </Row>
            </Container>
          </Row>
        </div>
      </div>
    );
  }
}

export const ConsolePage = connect<
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
})(ConsolePageComponent);
