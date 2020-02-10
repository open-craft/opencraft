import * as React from 'react';
import { INTERNAL_DOMAIN_NAME } from 'global/constants';
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

export class ConsolePageComponent extends React.PureComponent<Props> {
  public componentDidMount() {
    if (!this.props.loading && this.props.activeInstance.data === null) {
      this.props.listUserInstances();
    }
    setInterval(() => {
      if (this.props.activeInstance.data) {
        this.props.getDeploymentStatus(this.props.activeInstance.data.id);
      }
    }, 5000);
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
    const instanceLink =
      `https://${instanceData.subdomain}${INTERNAL_DOMAIN_NAME}` || '';
    const studioLink =
      `https://studio.${instanceData.subdomain}${INTERNAL_DOMAIN_NAME}` || '';

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
          <div className="loading">
            <i className="fas fa-2x fa-sync-alt fa-spin" />
          </div>
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

    return (
      <div className="console-page">
        {this.renderHeader()}

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

        <div className="console-page-container">
          <Row className="console-page-content">
            <Container fluid>
              <Row>
                <Col md="4">
                  <CustomizationSideMenu />
                </Col>
                <Col md="8" className="customization-form">
                  {content()}
                </Col>
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
