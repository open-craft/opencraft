const messages = {
  cancelRedeployment: {
    defaultMessage: 'Cancel deployment',
    description: 'Cancel deployment button.'
  },
  unavailable: {
    defaultMessage: 'Status: loading',
    description: 'Redeployment status.'
  },
  unavailableTooltip: {
    defaultMessage:
      'Instance status is being loaded, please wait a little bit.',
    description: 'Redeployment status tooltip text.'
  },
  runningDeployment: {
    defaultMessage: 'Status: deploying changes',
    description: 'Redeployment status.'
  },
  runningDeploymentTooltip: {
    defaultMessage:
      'Your instance is being updated with the latest settings. ' +
      'If you cancel this deployment, your changes wont be lost, ' +
      'but they will need to be redeployed.',
    description: 'Redeployment status tooltip text.'
  },
  updatedDeployment: {
    defaultMessage: 'Status: Up to date',
    description: 'Redeployment status.'
  },
  updatedDeploymentTooltip: {
    defaultMessage: 'Your instance is being updated with the latest settings.',
    description: 'Redeployment status tooltip text.'
  },
  preparingInstance: {
    defaultMessage: "Status: We're preparing your instance ",
    description: 'Redeployment status.'
  },
  preparingInstanceTooltip: {
    defaultMessage:
      'Your instance is being set-up, come back in a few hours to customize it.',
    description: 'Redeployment status tooltip text.'
  },
  pendingChanges: {
    defaultMessage: 'Status: Pending changes',
    description: 'Redeployment status.'
  },
  pendingChangesTooltip: {
    defaultMessage:
      "Your instance is up, but the latest settings aren't deployed yet.",
    description: 'Redeployment status tooltip text.'
  },
  failed: {
    defaultMessage: 'Status: Deployment error',
    description: 'Redeployment status.'
  },
  failedTooltip: {
    defaultMessage:
      'Your deployment failed. Our on-duty staff has been informed, and is ' +
      'starting to work on fixing it.',
    description: 'Redeployment status tooltip text.'
  }
};

export default messages;
