import * as React from 'react';
import { Col } from 'react-bootstrap';
import { ConsoleRoutes } from 'routes/console';
import './styles.scss';

export const ConsoleContainer: React.FC = () => (
  <Col className="console-container">
    <ConsoleRoutes />
  </Col>
);
