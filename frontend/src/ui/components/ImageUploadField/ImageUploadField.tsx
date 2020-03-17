import * as React from 'react';
import { Alert, Button, Modal } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import messages from './displayMessages';
import './styles.scss';

interface ImageUploadFieldProps {
  customUploadMessage: any;
  updateImage: Function;
  clearError: Function;
  recommendedSize?: string;
  error?: string;
  loading?: boolean;
}

export const ImageUploadField: React.FC<ImageUploadFieldProps> = (
  props: ImageUploadFieldProps
) => {
  const [show, setShow] = React.useState(false);
  const [image, setImage] = React.useState();

  const handleClose = () => setShow(false);
  const handleShow = () => {
    props.clearError();
    setShow(true);
  };

  const setImageIfValid = (files: any) => {
    // TODO: Add extension and file validation here
    // Currently the backend handles this
    setImage(files[0]);
  };

  return (
    <div className="image-upload-field">
      <h4>{props.customUploadMessage}</h4>
      {props.recommendedSize && (
        <p>
          <WrappedMessage messages={messages} id="recommendedSize" />
          {props.recommendedSize}
        </p>
      )}
      <Button
        variant="outline-primary"
        size="lg"
        onClick={handleShow}
        disabled={props.loading}
      >
        <WrappedMessage messages={messages} id="change" />
      </Button>

      {props.error && (
        <Alert className="error-box" variant="danger">
          {props.error}
        </Alert>
      )}

      <Modal
        show={show}
        onHide={handleClose}
        className="file-upload-modal"
        centered
      >
        <Modal.Header>
          <Modal.Title>
            <p>{props.customUploadMessage}</p>
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <input
            type="file"
            name="file"
            onChange={e => {
              setImageIfValid(e.target.files);
            }}
          />
        </Modal.Body>
        <Modal.Footer>
          <Button variant="outline-primary" size="lg" onClick={handleClose}>
            <WrappedMessage id="cancel" messages={messages} />
          </Button>
          <Button
            variant="primary"
            size="lg"
            onClick={() => {
              if (image) {
                props.updateImage(image);
              }
              handleClose();
            }}
          >
            <WrappedMessage id="updateImage" messages={messages} />
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};
