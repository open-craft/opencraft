import React from 'react';
import { WrappedMessage } from 'utils/intl';
import messages from './displayMessages';
import './styles.scss';

export const EmailActivationAlertMessage: React.FC = () => (
  <div className="d-flex justify-content-center align-middle email-activation-alert">
    <i className="alert-icon fas fa-exclamation-triangle fa-xs" />
    <WrappedMessage id="verifyEmail" messages={messages} />
  </div>
);
