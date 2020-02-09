import * as React from 'react';
import { WrappedMessage } from 'utils/intl';
import { Button, Modal } from 'react-bootstrap';
import { CustomStatusPill } from 'ui/components';
import { DeploymentInfoModel } from 'console/models';
import { OpenEdXInstanceDeploymentStatusStatusEnum } from 'ocim-client';
import messages from './displayMessages';
import './styles.scss';

interface Props {
  deployment?: DeploymentInfoModel;
  cancelRedeployment: Function;
  performDeployment: Function;
  loading: boolean;
}

export const RedeploymentToolbar: React.FC<Props> = (props: Props) => {
  const [show, setShow] = React.useState(false);

  const handleCloseModal = () => setShow(false);
  const handleShowModal = () => setShow(true);

  let deploymentDisabled: boolean = true;
  let undeployedChanges: number = 0;
  let deploymentStatus: OpenEdXInstanceDeploymentStatusStatusEnum =
    OpenEdXInstanceDeploymentStatusStatusEnum.NOSTATUS;

  if (props.deployment) {
    deploymentStatus = props.deployment.status;
    undeployedChanges = props.deployment.undeployedChanges;
    deploymentDisabled =
      props.loading ||
      !props.deployment.undeployedChanges ||
      props.deployment.status ===
        OpenEdXInstanceDeploymentStatusStatusEnum.DEPLOYING ||
      props.deployment.status ===
        OpenEdXInstanceDeploymentStatusStatusEnum.NOSTATUS ||
      props.deployment.status ===
        OpenEdXInstanceDeploymentStatusStatusEnum.PREPARINGINSTANCE;
  }

  return (
    <div className="d-flex justify-content-center align-middle redeployment-toolbar">
      <div className="redeployment-nav">
        <CustomStatusPill
          loading={props.loading}
          redeploymentStatus={deploymentStatus}
          cancelRedeployment={handleShowModal}
        />

        <Button
          className="float-right loading"
          variant="primary"
          size="lg"
          onClick={() => {
            props.performDeployment();
          }}
          disabled={deploymentDisabled}
        >
          <WrappedMessage
            id="deploy"
            messages={messages}
            values={{ undeployedChanges }}
          />
        </Button>
      </div>

      <Modal
        show={show}
        onHide={handleCloseModal}
        className="cancel-redeployment-modal"
        centered
      >
        <Modal.Header>
          <Modal.Title>
            <p>
              <WrappedMessage
                id="cancelDeploymentConfirm"
                messages={messages}
              />
            </p>
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <WrappedMessage
            id="cancelDeploymentConfirmText"
            messages={messages}
          />
        </Modal.Body>
        <Modal.Footer>
          <Button
            variant="outline-primary"
            size="lg"
            onClick={handleCloseModal}
          >
            <WrappedMessage id="closeModalButton" messages={messages} />
          </Button>
          <Button
            variant="primary"
            size="lg"
            onClick={() => {
              props.cancelRedeployment();
              handleCloseModal();
            }}
          >
            <WrappedMessage id="confirmCancelDeployment" messages={messages} />
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};
