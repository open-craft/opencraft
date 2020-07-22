import * as React from 'react';
import { connect } from 'react-redux';
import { RootState } from 'global/state';

import { OpenEdXInstanceDeploymentStatusStatusEnum as DeploymentStatus } from 'ocim-client';

import { Col, Collapse, Nav, Row } from 'react-bootstrap';

import { getNotifications } from 'console/actions';
import { DeploymentNotificationModel, InstancesModel } from 'console/models';
import { WrappedMessage } from 'utils/intl';

import messages from './displayMessages';
import { ConsolePage } from '../ConsolePage';

import './styles.scss';

interface ActionProps {
  getNotifications: Function;
}
interface Props extends ActionProps {
  activeInstance: InstancesModel['activeInstance'];
  notifications: Array<DeploymentNotificationModel>;
  loading: boolean;
}

interface NotificationProps {
  notification: DeploymentNotificationModel;
}

interface DeployedChangesProps {
  changes: DeploymentNotificationModel['deployedChanges'];
}

const DeployedChanges: React.FC<DeployedChangesProps> = (
  props: DeployedChangesProps
) => {
  const listItems: React.ReactNode[] = [];

  if (props.changes !== null) {
    props.changes.forEach(change => {
      const [changeType, whatChanged, changeContent] = change;

      if (changeType === 'change') {
        const [changeKey, changeValue] = changeContent;

        listItems.push(
          <li key={changeType + String(changeKey) + String(changeValue)}>
            <WrappedMessage
              id={changeType}
              messages={messages}
              values={{
                whatChanged: (
                  <span className="bg-light-gray">{whatChanged}</span>
                ),
                changeKey: <span className="bg-light-gray">{changeKey}</span>,
                changeValue: (
                  <span className="bg-light-gray">{changeValue}</span>
                )
              }}
            />
          </li>
        );
      }

      if (changeType === 'add' || changeType === 'remove') {
        // changeContent can't be string here, so
        // casting to array to satisfy typechecker
        Array(...changeContent).forEach(content => {
          const [key, value] = content;

          const messageId = whatChanged ? `${changeType}Existing` : changeType;
          listItems.push(
            <li key={changeType + String(key) + String(value)}>
              <WrappedMessage
                id={messageId}
                messages={messages}
                values={{
                  key: <span className="bg-light-gray">{key}</span>,
                  value: <span className="bg-light-gray">{value}</span>,
                  whatChanged: whatChanged ? (
                    <span className="bg-light-gray">{whatChanged}</span>
                  ) : null
                }}
              />
            </li>
          );
        });
      }
    });
  }

  return listItems.length ? (
    <ul>{listItems}</ul>
  ) : (
    <WrappedMessage id="noDetails" messages={messages} />
  );
};

const iconClassMap = {
  [DeploymentStatus.Healthy]: 'fa-check-circle text-primary',
  [DeploymentStatus.ChangesPending]: 'fa-check-circle text-primary',
  [DeploymentStatus.Provisioning]: 'fa-info-circle text-alert-yellow-2',
  [DeploymentStatus.Preparing]: 'fa-info-circle text-alert-yellow-2',
  [DeploymentStatus.Unhealthy]: 'fa-times-circle text-danger',
  [DeploymentStatus.Offline]: 'fa-stop-circle text-secondary'
};

const bgClassMap = {
  [DeploymentStatus.Healthy]: 'bg-light-blue',
  [DeploymentStatus.ChangesPending]: 'bg-light-blue',
  [DeploymentStatus.Provisioning]: 'bg-alert-yellow-1',
  [DeploymentStatus.Preparing]: 'bg-alert-yellow-1',
  [DeploymentStatus.Unhealthy]: 'bg-alert-red',
  [DeploymentStatus.Offline]: 'bg-light-gray'
};

const Notification: React.FC<NotificationProps> = (
  props: NotificationProps
) => {
  const [open, setOpen] = React.useState(false);

  const deploymentStatus = props.notification.status;

  const bgClass = bgClassMap[deploymentStatus];
  const caretClass = open ? 'fa-caret-up' : 'fa-caret-down';
  const iconClass = iconClassMap[deploymentStatus];

  const date = props.notification.date.toLocaleDateString('default', {
    month: 'long',
    year: 'numeric',
    day: 'numeric'
  });

  return (
    <div className="deployment-notification mb-3">
      <div className={`p-3 d-flex deployment-notification-header ${bgClass}`}>
        <div className="d-flex">
          <i className={`mr-3 align-self-center fa ${iconClass}`} />
        </div>
        <div>
          <p className="m-0 deployment-notification-message text-secondary-1">
            <WrappedMessage id={deploymentStatus} messages={messages} />
          </p>
          <p className="m-0 deployment-notification-date text-secondary-2">
            <small>{date}</small>
          </p>
        </div>
        <Nav.Link
          className="d-flex expand-caret-button ml-auto text-primary"
          onClick={() => setOpen(!open)}
          onKeyDown={() => setOpen(!open)}
        >
          <i className={`align-self-center fa ${caretClass}`} />
        </Nav.Link>
      </div>
      <Collapse in={open}>
        <div className={`deployment-notification-body ${bgClass}`}>
          <div className="p-3 align-middle">
            <DeployedChanges changes={props.notification.deployedChanges} />
          </div>
        </div>
      </Collapse>
    </div>
  );
};

const NoticeBoardComponent: React.FC<Props> = (props: Props) => {
  React.useEffect(
    () => {
      props.getNotifications();
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  const notifications = props.notifications.map(notification => (
    <Notification
      key={notification.date.toString() + notification.status.toString()}
      notification={notification}
    />
  ));

  let isEmailVerified = true;
  if (props.activeInstance && props.activeInstance.data) {
    isEmailVerified = props.activeInstance.data.isEmailVerified;
  }

  const pageContent = isEmailVerified ? (
    notifications
  ) : (
    <p>
      <WrappedMessage id="noActiveInstance" messages={messages} />
    </p>
  );

  return (
    <ConsolePage showSidebar={false} contentLoading={props.loading}>
      <Row className="justify-content-center">
        <Col md={7}>
          <div className="notice-board-heading">
            <p>
              <WrappedMessage id="noticeBoard" messages={messages} />
            </p>
          </div>
          {pageContent}
        </Col>
      </Row>
    </ConsolePage>
  );
};

export const NoticeBoard = connect<{}, ActionProps, {}, Props, RootState>(
  (state: RootState) => ({
    activeInstance: state.console.activeInstance,
    notifications: state.console.notifications,
    loading: state.console.notificationsLoading
  }),
  {
    getNotifications
  }
)(NoticeBoardComponent);
