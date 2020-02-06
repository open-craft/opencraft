import * as React from 'react';
import { WrappedMessage } from 'utils/intl';
import { Tooltip, OverlayTrigger, Badge, Nav } from 'react-bootstrap';
import { OpenEdXInstanceDeploymentStatusStatusEnum } from 'ocim-client';

import messages from './displayMessages';
import './styles.scss';

interface Props {
  redeploymentStatus: string;
  cancelRedeployment: Function;
}

export const CustomStatusPill: React.FC<Props> = (props: Props) => {
  let dotColor = 'grey';
  let deploymentStatusText = 'unavailable';
  let tooltipText = 'unavailableTooltip';

  switch (props.redeploymentStatus) {
    case OpenEdXInstanceDeploymentStatusStatusEnum.UPTODATE:
      dotColor = '#1abb64';
      deploymentStatusText = 'updatedDeployment';
      tooltipText = 'updatedDeploymentTooltip';
      break;
    case OpenEdXInstanceDeploymentStatusStatusEnum.DEPLOYING:
      dotColor = '#ff9b04';
      deploymentStatusText = 'runningDeployment';
      tooltipText = 'runningDeploymentTooltip';
      break;
    case OpenEdXInstanceDeploymentStatusStatusEnum.PREPARINGINSTANCE:
      dotColor = '#ff9b04';
      deploymentStatusText = 'preparingInstance';
      tooltipText = 'preparingInstanceTooltip';
      break;
    case OpenEdXInstanceDeploymentStatusStatusEnum.PENDINGCHANGES:
      dotColor = '#1abb64';
      deploymentStatusText = 'pendingChanges';
      tooltipText = 'pendingChangesTooltip';
      break;
    default:
      // Default values already set up when instancing variables
      break;
  }

  const tooltip = (
    <Tooltip id="redeployment-status">
      <WrappedMessage messages={messages} id={tooltipText} />
    </Tooltip>
  );

  return (
    <OverlayTrigger placement="right" overlay={tooltip}>
      <Badge pill className="status-pill" variant="primary">
        <span className="dot" style={{ backgroundColor: dotColor }} />
        <div className="text">
          <WrappedMessage id={deploymentStatusText} messages={messages} />
        </div>
        {props.redeploymentStatus ===
          OpenEdXInstanceDeploymentStatusStatusEnum.DEPLOYING && (
          <Nav
            className="text cancel-deployment"
            onClick={() => {
              props.cancelRedeployment();
            }}
          >
            <i className="fas fa-xs fa-times" />
            <WrappedMessage id="cancelRedeployment" messages={messages} />
          </Nav>
        )}
      </Badge>
    </OverlayTrigger>
  );
};
