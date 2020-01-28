import * as React from 'react';
import { WrappedMessage } from 'utils/intl';
import { Button, Modal } from 'react-bootstrap';
import { RedeploymentStatus } from 'global/constants';
import { CustomStatusPill } from 'ui/components';
import messages from './displayMessages';
import './styles.scss';

interface Props {
  redeploymentStatus: string;
  numberOfChanges: number;
  cancelRedeployment: Function;
  performDeployment: Function;
}

export const RedeploymentToolbar: React.FC<Props> = (props: Props) => {
  const [show, setShow] = React.useState(false);

  const handleCloseModal = () => setShow(false);
  const handleShowModal = () => setShow(true);

  const redeploymentDisabled =
    !props.numberOfChanges ||
    props.redeploymentStatus === RedeploymentStatus.DEPLOYING ||
    props.redeploymentStatus === RedeploymentStatus.NO_STATUS ||
    props.redeploymentStatus === RedeploymentStatus.CANCELLING_DEPLOYMENT;

  return (
    <div className="d-flex justify-content-center align-middle redeployment-toolbar">
      <div className="redeployment-nav">
        <CustomStatusPill
          redeploymentStatus={props.redeploymentStatus}
          cancelRedeployment={handleShowModal}
        />

        <Button
          className="float-right loading"
          variant="primary"
          size="lg"
          onClick={() => {
            handleShowModal();
          }}
          disabled={redeploymentDisabled}
        >
          <WrappedMessage
            id="deploy"
            messages={messages}
            values={{ numberOfChanges: props.numberOfChanges }}
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
            <p>Are you sure you want to cancel this redeployment?</p>
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          Your instance is being updated with the latest settings. If you cancel
          this deployment, your changes wont be lost, but they will need to be
          redeployed.
        </Modal.Body>
        <Modal.Footer>
          <Button
            variant="outline-primary"
            size="lg"
            onClick={handleCloseModal}
          >
            Close
          </Button>
          <Button variant="primary" size="lg" onClick={handleCloseModal}>
            Cancel redeployment
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};
