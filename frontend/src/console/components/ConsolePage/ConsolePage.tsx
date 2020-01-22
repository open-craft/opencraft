import * as React from 'react';
import { RedeploymentToolbar, CustomizationSideMenu } from 'console/components';
import { Row, Col, Container } from 'react-bootstrap';

import './styles.scss';

interface Props {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  titleExtra?: React.ReactNode;
}

export const ConsolePage: React.FC<Props> = (props: Props) => {
  const instanceLink = 'https://courses.opencraft.hosting';
  const studioLink = 'https://studio.courses.opencraft.hosting';
  const instanceName = (
    <a className="header-link" href={instanceLink}>
      Wellington High School
      <div className="instance-link" />
    </a>
  );
  const instanceStudioLink = (
    <a className="header-link" href={studioLink}>
      Edit courses (Studio)
    </a>
  );

  return (
    <div className="console-page">
      <div className="title-container">
        <h1>{instanceName}</h1>
        <h2>{instanceStudioLink}</h2>
      </div>

      <RedeploymentToolbar />

      <div className="console-page-container">
        <Row className="console-page-content">
          <Container fluid>
            <Row>
              <Col md="4">
                <CustomizationSideMenu />
              </Col>
              <Col md="8">{props.children}</Col>
            </Row>
          </Container>
        </Row>
      </div>
    </div>
  );
};
