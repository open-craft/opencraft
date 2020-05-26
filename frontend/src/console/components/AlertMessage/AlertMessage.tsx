import React from 'react';
import { Alert } from 'react-bootstrap';
import './styles.scss';
import { WrappedMessage } from 'utils/intl';
import messages from './displayMessages';

export const AlertMessage: React.FC = () => (
  <Alert
    className="d-flex justify-content-center align-middle alert-warning"
    variant="warning"
  >
    <WrappedMessage id="verifyEmail" messages={messages} />
  </Alert>
);
