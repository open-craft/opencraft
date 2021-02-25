import React from 'react';
import {
  SUPPORT_LINK,
  CONTACT_US_LINK,
  PRIVACY_POLICY_LINK,
  OPENCRAFT_WEBSITE_LINK
} from 'global/constants';
import { Col, Row } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import messages from './displayMessages';
import './styles.scss';

export const Footer: React.FC = () => (
  <Row fluid="true" as="footer" className="app-footer align-items-center py-4">
    <Col lg="auto" sm={{ span: 12 }} className="text-center mx-2 my-2 ">
      <a
        className="footer-link"
        href={OPENCRAFT_WEBSITE_LINK}
        target="_blank"
        rel="noopener noreferrer"
      >
        How we work
      </a>
    </Col>
    <Col lg="auto" sm={{ span: 12 }} className="text-center mx-2 my-2">
      <a className="footer-link" href={SUPPORT_LINK}>
        Support
      </a>
    </Col>
    <Col lg="auto" sm={{ span: 12 }} className="text-center mx-2 my-2">
      <a className="footer-link" href={CONTACT_US_LINK}>
        Contact
      </a>
    </Col>
    <Col lg="auto" sm={{ span: 12 }} className="text-center mx-2 my-2">
      <a className="footer-link" href={PRIVACY_POLICY_LINK}>
        Privacy
      </a>
    </Col>
    <Col
      lg="auto"
      sm={{ span: 12 }}
      className="copyright-trademarks text-center text-lg-right ml-auto mt-5 mt-lg-0"
    >
      <WrappedMessage id="copyright" messages={messages} />
      <span className="mx-2">|</span>
      <WrappedMessage id="trademarks" messages={messages} />
    </Col>
  </Row>
);
