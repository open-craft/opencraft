import * as React from 'react';
import { Toast } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import './styles.scss';

interface Props {
  show: boolean;
  onClose: () => void;
  delay: number;
  autohide: boolean;
  bodyMessageId: string;
  closeMessage: string;
  messages: any;
}

export const NotificationToast: React.FC<Props> = ({
  show,
  onClose,
  delay,
  autohide,
  bodyMessageId,
  closeMessage,
  messages
}: Props) => {
  return (
    <div className="toast-container">
      <Toast
        className="deployToast"
        show={show}
        onClose={onClose}
        delay={delay}
        autohide={autohide}
      >
        <Toast.Header className="toast-header" closeLabel={closeMessage} />
        <Toast.Body>
          <WrappedMessage id={bodyMessageId} messages={messages} />
        </Toast.Body>
      </Toast>
    </div>
  );
};
