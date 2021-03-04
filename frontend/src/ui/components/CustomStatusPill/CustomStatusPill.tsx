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
  const { tooltipText, pillColor, deploymentStatusText } = buildStatusContext(
    redeploymentStatus,
    deploymentType
  );
  const tooltip = (
    <Tooltip id="redeployment-status">
      <WrappedMessage messages={messages} id={tooltipText} />
    </Tooltip>
  );

  return (
    <Badge
      pill
      className="status-pill"
      variant="primary"
      style={{ backgroundColor: pillColor }}
    >
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
      <OverlayTrigger placement="right" overlay={tooltip}>
        <i className="fas fa-question-circle fa-lg" />
      </OverlayTrigger>
    </Badge>
  );
};
