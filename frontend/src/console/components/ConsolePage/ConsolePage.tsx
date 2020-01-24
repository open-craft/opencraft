import * as React from 'react';
import { RedeploymentToolbar, CustomizationSideMenu } from 'console/components';
import { Row, Col, Container } from 'react-bootstrap';
import { InstanceSettingsModel } from '../models';

import './styles.scss';

interface Props {
  children: React.ReactNode;
  loading: boolean;
  titleExtra?: React.ReactNode;
  instanceSettings?: InstanceSettingsModel;
}

export const ConsolePage: React.FC<Props> = (props: Props) => {
  const instanceName = () => {
      if (props.instanceSettings) {
        let instanceLink = props.instanceSettings.internalDomainName || ""
        if (props.instanceSettings.externalDomainName) {
          instanceLink = props.instanceSettings.externalDomainName
        }
        return (
          <a className="header-link" href={instanceLink}>
            {props.instanceSettings.instanceName}
            <div className="instance-link" />
          </a>
        );
      } else {
        return (
          <div />
        )
      };
  };

  const instanceStudioLink = () => {
      if (props.instanceSettings) {
        let studioLink = props.instanceSettings.internalStudioDomainName || ""
        if (props.instanceSettings.externalStudioDomainName) {
          studioLink = props.instanceSettings.externalStudioDomainName
        }
        return (
          <a className="header-link" href={studioLink}>
            Edit courses (Studio)
          </a>
        );
      } else {
        return (
          <div />
        )
      };
  };

  const content = () => {
    if (props.loading) {
      return (
        <div className="loading">
          <i className="fas fa-2x fa-sync-alt fa-spin"></i>
        </div>
      )
    } else {
      return props.children
    }
  }

  return (
    <div className="console-page">
      <div className="title-container">
        <h1>{instanceName()}</h1>
        <h2>{instanceStudioLink()}</h2>
      </div>

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
