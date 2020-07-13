import { OpenEdXInstanceDeploymentStatusStatusEnum as DeploymentStatus } from 'ocim-client';

const messages = {
  [DeploymentStatus.Healthy]: {
    defaultMessage: 'Deployment successful.',
    description: 'Redeployment alert message.'
  },
  [DeploymentStatus.ChangesPending]: {
    defaultMessage: 'Deployment successful, changes pending.',
    description: 'Redeployment alert message.'
  },
  [DeploymentStatus.Unhealthy]: {
    defaultMessage: 'Deployment error.',
    description: 'Redeployment alert message.'
  },
  [DeploymentStatus.Provisioning]: {
    defaultMessage: 'Deployment in progress: provisioning.',
    description: 'Redeployment alert message.'
  },
  [DeploymentStatus.Preparing]: {
    defaultMessage: 'Deployment in progress: preparing.',
    description: 'Redeployment alert message.'
  },
  [DeploymentStatus.Offline]: {
    defaultMessage: 'Deployment offline.',
    description: 'Redeployment alert message.'
  },
  noticeBoard: {
    defaultMessage: 'Notice Board',
    description: 'Notice board heading.'
  },
  noDetails: {
    defaultMessage: 'No redeployment details.',
    description:
      'Message for alert when redeployment has no changes or details.'
  },
  add: {
    defaultMessage: 'Added {key} with value {value}',
    description: 'Message for `added` type of change.'
  },
  remove: {
    defaultMessage: 'Removed {key} with value {value}',
    description: 'Message for `removed` type of change.'
  },
  addExisting: {
    defaultMessage: 'Added {key} with value {value} in {whatChanged}',
    description: 'Message for `added` type of change for existing variable.'
  },
  removeExisting: {
    defaultMessage: 'Removed {key} with value {value} from {whatChanged}',
    description: 'Message for `removed` type of change for existing variable.'
  },
  change: {
    defaultMessage: 'Changed {whatChanged} from {changeKey} to {changeValue}',
    description: 'Message for `changed` type of change.'
  }
};

export default messages;
