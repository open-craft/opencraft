import * as React from 'react';
import { Row } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import messages from './displayMessages';
import './styles.scss';

export const ErrorPage: React.FC = () => (
  <div className="error-page">
    <div className="error-container">
      <Row className="error-page-content">
        <p>
          <WrappedMessage id="somethingWrong" messages={messages} />
        </p>
        <WrappedMessage id="errorMessage" messages={messages} />
      </Row>
    </div>
  </div>
);
