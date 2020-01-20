import * as React from 'react';
import { ContentPage } from 'ui/components';
import { RedeploymentToolbar } from 'console/components';
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
    <ContentPage
      title={instanceName}
      subtitle={instanceStudioLink}
      toolbar={<RedeploymentToolbar />}
    >
      <Container fluid>
        <Row>
          <Col>Menu</Col>
          <Col>{props.children}</Col>
        </Row>
      </Container>
    </ContentPage>
  );
};
