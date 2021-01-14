import * as React from 'react';
import { WrappedMessage } from 'utils/intl';
import { Tooltip, OverlayTrigger, Badge, Nav } from 'react-bootstrap';
import { OpenEdXInstanceDeploymentStatusStatusEnum as DeploymentStatus } from 'ocim-client';
import { buildStatusContext } from './util';
import messages from './displayMessages';
import './styles.scss';

interface Props {
  loading: boolean;
  redeploymentStatus: string | null;
  deploymentType: string | null;
  cancelRedeployment: Function | undefined;
}

export const CustomStatusPill: React.FC<Props> = ({
  loading,
  redeploymentStatus,
  deploymentType,
  cancelRedeployment
}: Props) => {
  const { tooltipText, dotColor, deploymentStatusText } = buildStatusContext(
    redeploymentStatus,
    deploymentType
  );

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
        {cancelRedeployment !== undefined &&
          redeploymentStatus === DeploymentStatus.Provisioning &&
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
