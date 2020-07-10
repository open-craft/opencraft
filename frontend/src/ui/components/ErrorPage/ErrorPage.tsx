import * as React from 'react';
import { Row } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import messages from './displayMessages';
import './styles.scss';

interface ErrorPageProps {
  messages?: any;
  messageId?: string;
  values?: any;
}

export const ErrorPage: React.FC<ErrorPageProps> = (props: ErrorPageProps) => {
  let body;
  if (props.messages && props.messageId) {
    body = (
      <WrappedMessage
        id={props.messageId}
        messages={props.messages}
        values={props.values}
      />
    );
  } else {
    body = (
      <>
        <p>
          <WrappedMessage id="somethingWrong" messages={messages} />
        </p>
        <WrappedMessage id="errorMessage" messages={messages} />
      </>
    );
  }
  return (
    <div className="error-page">
      <div className="error-container">
        <Row className="error-page-content">{body}</Row>
      </div>
    </div>
  );
};
