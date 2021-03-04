import {
  OpenEdXInstanceDeploymentStatusStatusEnum as DeploymentStatus,
  OpenEdXInstanceDeploymentStatusDeploymentTypeEnum as DeploymentType
} from 'ocim-client';

interface StatusContext {
  tooltipText: string;
  pillColor: string;
  deploymentStatusText: string;
}

/**
 * An utility function to conditionally return color, tooltip and
 * status text keys based on deployment status and type.
 *
 * @param redeploymentStatus
 * @param deploymentType
 * @returns StatusContext
 */
export function buildStatusContext(
  redeploymentStatus?: string | null,
  deploymentType?: string | null
): StatusContext {
  const result: StatusContext = {
    pillColor: 'grey',
    deploymentStatusText: 'unavailable',
    tooltipText: 'unavailableTooltip'
  };

  switch (redeploymentStatus) {
    case DeploymentStatus.Healthy:
      result.pillColor = '#00a556';
      result.deploymentStatusText = 'updatedDeployment';
      result.tooltipText = 'updatedDeploymentTooltip';
      break;
    case DeploymentStatus.Provisioning:
      result.pillColor = '#ff9b04';
      // If there's a deployment provisioning, but it's the
      // first on (from registration), show preparing instance
      // message.
      if (deploymentType === DeploymentType.Registration) {
        result.deploymentStatusText = 'preparingInstance';
        result.tooltipText = 'preparingInstanceTooltip';
      }

      // If not, then this is a normal deployment, so show the usual
      // running deployment message.
      else {
        result.deploymentStatusText = 'runningDeployment';
        result.tooltipText = 'runningDeploymentTooltip';
      }
      break;
    case DeploymentStatus.Preparing:
      result.pillColor = '#ff9b04';
      result.deploymentStatusText = 'preparingInstance';
      result.tooltipText = 'preparingInstanceTooltip';
      break;
    case DeploymentStatus.ChangesPending:
      result.pillColor = '#00a556';
      result.deploymentStatusText = 'pendingChanges';
      result.tooltipText = 'pendingChangesTooltip';
      break;
    default:
      // Default values already set up when instancing variables
      break;
  }
  return result;
}
