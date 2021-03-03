import * as React from 'react';
import { WrappedMessage } from 'utils/intl';
import { Button } from 'react-bootstrap';
import messages from './displayMessages';
import './styles.scss';

interface Props {
  deploymentDisabled: boolean;
  undeployedChanges: number;
  deploymentHandler: Function;
}

export const PublishButton: React.FC<Props> = ({
  deploymentDisabled,
  undeployedChanges,
  deploymentHandler
}: Props) => {
  const notificationNumber = undeployedChanges <= 9 ? undeployedChanges : '9+';

  return (
    <Button
      className={
        deploymentDisabled
          ? 'float-right btn-disabled'
          : 'float-right btn-enabled'
      }
      variant="primary"
      size="lg"
      disabled={deploymentDisabled}
      onClick={() => {
        deploymentHandler();
      }}
    >
      {undeployedChanges !== 0 && (
        <div className="notification-layer">
          <p>
            <WrappedMessage
              id="notificationText"
              messages={messages}
              values={{ notificationNumber }}
            />
          </p>
        </div>
      )}
      <div className="button-text-layer">
        <WrappedMessage id="deploy" messages={messages} />
      </div>
    </Button>
  );
};
