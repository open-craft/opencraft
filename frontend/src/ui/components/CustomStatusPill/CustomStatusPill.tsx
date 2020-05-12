import * as React from 'react';
import { WrappedMessage } from 'utils/intl';
import { Tooltip, OverlayTrigger, Badge, Nav } from 'react-bootstrap';
import { OpenEdXInstanceDeploymentStatusStatusEnum as DeploymentStatus} from 'ocim-client';

import messages from './displayMessages';
import './styles.scss';

interface Props {
  loading: boolean;
  redeploymentStatus: string | null;
  cancelRedeployment: Function;
}

export const CustomStatusPill: React.FC<Props> = ({loading, redeploymentStatus, cancelRedeployment}) => {
  let dotColor = 'grey';
  let deploymentStatusText = 'unavailable';
  let tooltipText = 'unavailableTooltip';

  switch (redeploymentStatus) {
    case DeploymentStatus.Healthy:
      dotColor = '#1abb64';
      deploymentStatusText = 'updatedDeployment';
      tooltipText = 'updatedDeploymentTooltip';
      break;
    case DeploymentStatus.Provisioning:
      dotColor = '#ff9b04';
      deploymentStatusText = 'runningDeployment';
      tooltipText = 'runningDeploymentTooltip';
      break;
    case DeploymentStatus.Preparing:
      dotColor = '#ff9b04';
      deploymentStatusText = 'preparingInstance';
      tooltipText = 'preparingInstanceTooltip';
      break;
    case DeploymentStatus.ChangesPending:
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
        {redeploymentStatus === DeploymentStatus.Provisioning &&
          !loading && (
            <Nav
              className="text cancel-deployment"
              onClick={() => {
                cancelRedeployment();
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
