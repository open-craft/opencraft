import * as React from 'react';
import { Alert, Button, Modal, OverlayTrigger, Tooltip } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import upArrowIcon from 'assets/uparrow.png';
import messages from './displayMessages';
import './styles.scss';

interface ImageUploadFieldProps {
  customUploadMessage: any;
  updateImage: Function;
  clearError: Function;
  parentMessages?: any;
  recommendationTextId?: string;
  error?: string;
  loading?: boolean;
  reset?: Function;
  tooltipTextId?: string;
  tooltipImage?: string;
  innerPreview?: string;
}

interface Image {
  name?: string;
}

export const ImageUploadField: React.FC<ImageUploadFieldProps> = (
  props: ImageUploadFieldProps
) => {
  const [show, setShow] = React.useState(false);
  const [image, setImage] = React.useState();

  const filename = (file: Image | undefined) => {
    if (file) {
      return file.name;
    }
    return '';
  };

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

  const buttonContents = () => {
    /* eslint-disable react/prop-types */
    if (props.innerPreview) {
      const img = new Image();
      img.src = props.innerPreview;
      if (img.height !== 0) {
        return (
          <div className="image-container">
            <img src={props.innerPreview} alt="preview" />
          </div>
        );
      }
    }
    return (
      <div>
        <img className="upload-icon" src={upArrowIcon} alt="Upload icon" />
        <h4>
          <WrappedMessage messages={messages} id="change" />
        </h4>
      </div>
    );
  };

  let tooltip = null;

  if (props.parentMessages && props.tooltipTextId) {
    tooltip = (
      <Tooltip className="image-upload-tooltip" id={props.tooltipTextId}>
        <p>
          <WrappedMessage
            messages={props.parentMessages}
            id={props.tooltipTextId}
          />
        </p>
        {props.tooltipImage && (
          <img
            className="tooltip-image"
            src={props.tooltipImage}
            alt="tooltipImage"
          />
        )}
      </Tooltip>
    );
  }

  return (
    <div className="image-upload-field">
      <div className="component-header">
        <h4 className="upload-field-header">{props.customUploadMessage}</h4>
        {tooltip && (
          <OverlayTrigger placement="top" overlay={tooltip}>
            <i className="fas fa-info-circle" />
          </OverlayTrigger>
        )}
      </div>
      <Button
        variant="outline-primary"
        size="lg"
        onClick={handleShow}
        disabled={props.loading}
        className="upload-button"
      >
        <div className="button-contents">{buttonContents()}</div>
      </Button>
      {props.parentMessages && props.recommendationTextId && (
        <p>
          <WrappedMessage
            messages={props.parentMessages}
            id={props.recommendationTextId}
          />
        </p>
      )}
      <h3>{filename(image)}</h3>
      {props.error && (
        <Alert className="error-box" variant="danger">
          <p>{props.error}</p>
        </Alert>
      )}

      {props.reset !== undefined && (
        <p>
          <button
            className="reset-image"
            type="button"
            onClick={() => {
              // Using `!` because we know this will never be called
              // if props.reset is undefined (this component won't be
              // rendered).
              props.reset!();
            }}
          >
            Remove
          </button>
        </p>
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
            accept="image/*"
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
