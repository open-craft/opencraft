const messages = {
  cancelRedeployment: {
    defaultMessage: 'Cancel deployment',
    description: 'Cancel deployment button.'
  },
  unavailable: {
    defaultMessage: 'Loading',
    description: 'Redeployment status.'
  },
  unavailableTooltip: {
    defaultMessage:
      'Instance status is being loaded, please wait a little bit.',
    description: 'Redeployment status tooltip text.'
  },
  runningDeployment: {
    defaultMessage: 'Publishing',
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
    defaultMessage: 'Up to date',
    description: 'Redeployment status.'
  },
  updatedDeploymentTooltip: {
    defaultMessage: 'Your instance is running with the latest settings.',
    description: 'Redeployment status tooltip text.'
  },
  preparingInstance: {
    defaultMessage: 'Publishing',
    description: 'Redeployment status.'
  },
  preparingInstanceTooltip: {
    defaultMessage:
      'Your updates are publishing to your live site (LMS). This can take 2-3 hours',
    description: 'Redeployment status tooltip text.'
  },
  pendingChanges: {
    defaultMessage: 'Publishing',
    description: 'Redeployment status.'
  },
  pendingChangesTooltip: {
    defaultMessage:
      "Your instance is up, but the latest settings aren't deployed yet.",
    description: 'Redeployment status tooltip text.'
  },
  failed: {
    defaultMessage: 'Deployment error',
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
