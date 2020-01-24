import * as React from 'react';
import { INTERNAL_DOMAIN_NAME } from 'global/constants';
import { RedeploymentToolbar, CustomizationSideMenu } from 'console/components';
import { Row, Col, Container } from 'react-bootstrap';
import { InstancesModel } from 'console/models';
import { RootState } from 'global/state';
import { connect } from 'react-redux';
import { listUserInstances } from 'console/actions';

import './styles.scss';


interface ActionProps {
  listUserInstances: Function;
}

interface StateProps extends InstancesModel {}
interface Props extends StateProps, ActionProps {
  children: React.ReactNode;
  contentLoading: boolean;
}

export class ConsolePageComponent extends React.PureComponent<Props> {
  private renderHeader() {
    if (this.props.loading || (this.props.selectedInstance === null)) {
      return (
        <div className="title-container">
          <h1>
            <i className="fas fa-sync-alt fa-spin"></i>
          </h1>
        </div>
      )
    } else {
      let instanceData = this.props.instances[this.props.selectedInstance];
      let instanceLink = `https://${instanceData.subdomain}${INTERNAL_DOMAIN_NAME}` || "";
      let studioLink = `https://studio.${instanceData.subdomain}${INTERNAL_DOMAIN_NAME}` || "";

      return (
        <div className="title-container">
          <h1>
            <a className="header-link" href={instanceLink}>
              {instanceData.instanceName}
              <i className="instance-link fas fa-link fa-xs"></i>
            </a>
          </h1>
          <h2>
            <a className="header-link" href={studioLink}>
              Edit courses (Studio)
            </a>
          </h2>
        </div>
      );
    }
  }

  public render() {
    console.log(this.props)
    if (!this.props.loading && this.props.selectedInstance === null) {
      this.props.listUserInstances()
    }


    const content = () => {
      if (this.props.contentLoading) {
        return (
          <div className="loading">
            <i className="fas fa-2x fa-sync-alt fa-spin"></i>
          </div>
        )
      } else {
        return this.props.children
      }
    }

    return (
      <div className="console-page">
        {this.renderHeader()}

        <RedeploymentToolbar />

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
  };
};

export const ConsolePage = connect<StateProps, ActionProps, {}, Props, RootState>(
  (state: RootState) => ({
    ...state.console
  }),
  {
    listUserInstances
  }
)(ConsolePageComponent);
