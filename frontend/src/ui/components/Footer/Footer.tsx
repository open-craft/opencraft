import React from 'react';
import { Col, Row } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import messages from './displayMessages';
import './styles.scss';

export const Footer: React.FC = () => (
  <Row as="footer" className="app-footer align-items-center">
    <Col className="col-auto mr-auto">
      <WrappedMessage id="copyright" messages={messages} />
    </Col>
    <Col className="col-auto">
      <WrappedMessage id="trademarks" messages={messages} />
    </Col>
  </Row>
);
