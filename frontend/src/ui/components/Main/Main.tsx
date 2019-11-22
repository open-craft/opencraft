import * as React from 'react';
import { Row } from 'react-bootstrap';
import { MainRoutes } from '../../../routes';
import './styles.scss';


export const Main: React.FC = () => (
  <Row className="app-main">
    <MainRoutes />
  </Row>
);
