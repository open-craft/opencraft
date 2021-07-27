import * as React from 'react';
import { Alert, Button, Modal, OverlayTrigger, Tooltip } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import upArrowIcon from 'assets/uparrow.png';
import messages from './displayMessages';
import './styles.scss';

interface ModalImageInputProps {
  customUploadMessage: any;
  clearError: () => void;
  error?: string;
  innerPreview?: string;
  loading?: boolean;
  parentMessages?: any;
  recommendationTextId?: string;
  reset?: Function;
  updateImage: Function;
}

interface ImageUploadFieldProps extends ModalImageInputProps {
  tooltipTextId?: string;
  tooltipImage?: string;
}

interface Image {
  name?: string;
}

export const ModalImageInput: React.FC<ModalImageInputProps> = (
  props: ModalImageInputProps
) => {
  const [show, setShow] = React.useState(false);
  const [image, setImage] = React.useState();

  const handleClose = () => setShow(false);
  const handleShow = () => {
    props.clearError();
    setShow(true);
  };

  const filename = (file: Image | undefined) => {
    if (file) {
      return file.name;
    }
    return '';
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
  return (
    <>
      <Button
        variant="outline-primary"
        size="lg"
        onClick={handleShow}
        disabled={props.loading}
        className="upload-button"
      >
        <div className="button-contents">{buttonContents()}</div>
      </Button>
      {props.innerPreview && (
        <Button
          variant="link"
          color="link"
          size="sm"
          onClick={handleShow}
          disabled={props.loading}
          className="link-button"
        >
          <p>
            <WrappedMessage messages={messages} id="changeLink" />
          </p>
        </Button>
      )}
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
    </>
  );
};

/**
 * @deprecated Use ModalImageInput instead
 */
export const ImageUploadField: React.FC<ImageUploadFieldProps> = (
  props: ImageUploadFieldProps
) => {
  let tooltip = null;

  if (props.parentMessages && props.tooltipTextId) {
    tooltip = (
      <OverlayTooltip
        id={props.tooltipTextId}
        innerPreview={props.innerPreview}
        tooltipImage={props.tooltipImage}
      >
        <WrappedMessage
          messages={props.parentMessages}
          id={props.tooltipTextId}
        />
      </OverlayTooltip>
    );
  }

  return (
    <div className="image-upload-field">
      <div className="component-header">
        <h4 className="upload-field-header">
          {props.customUploadMessage}
          {tooltip}
        </h4>
      </div>
      <ModalImageInput {...props} />
    </div>
  );
};

interface OverlayTooltipProps {
  id: string;
  tooltipImage?: string;
  innerPreview?: string;
  children: React.ReactNode;
}
export const OverlayTooltip: React.FC<OverlayTooltipProps> = props => {
  const tooltip = (
    <Tooltip className="image-upload-tooltip" id={props.id}>
      <p>{props.children}</p>
      {props.tooltipImage && (
        <img
          className="tooltip-image"
          src={props.tooltipImage}
          alt="tooltipImage"
        />
      )}
    </Tooltip>
  );
  return (
    <OverlayTrigger placement="top" overlay={tooltip}>
      <i className="fas fa-info-circle" />
    </OverlayTrigger>
  );
};
