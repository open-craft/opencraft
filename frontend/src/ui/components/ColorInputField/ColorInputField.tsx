import * as React from 'react';
import {
  FormControl,
  FormGroup,
  FormLabel,
  Tooltip,
  OverlayTrigger,
  Row
} from 'react-bootstrap';

import { SketchPicker } from 'react-color';
import { WrappedMessage } from 'utils/intl';
import { messages as internalMessages } from './displayMessages';
import './styles.scss';

interface ColorInputFieldProps {
  fieldName: string;
  genericFieldName?: string;
  initialValue?: string;
  onChange?: any;
  error?: string;
  messages: any;
  loading?: boolean;
  hideTooltip?: boolean;
}

export const ColorInputField: React.FC<ColorInputFieldProps> = (
  props: ColorInputFieldProps
) => {
  const pickerContainer = React.useRef<HTMLDivElement>(null);
  const [colorPicker, setColorPicker] = React.useState(false);
  const [selectedColor, setColor] = React.useState(props.initialValue);

  // Get name that can be used with generic displayMessages.
  const genericFieldName = props.genericFieldName || props.fieldName;

  const toggleColorPicker = () => {
    setColorPicker(!colorPicker);
  };

  const resetColor = () => {
    // This will reset the field value to the default theme value
    // TODO: this will need to be updated when the Theme configuration endpoint
    // get updated to improve consistency
    props.onChange(props.fieldName, '');
  };

  /**
   * Using effect dependent on color to update bound functions
   * when the color is changed, otherwise it would always pick
   * props.initialColor and never made the request.
   */
  React.useEffect(() => {
    const hideColorPickerAndSubmit = () => {
      setColorPicker(false);

      if (selectedColor !== props.initialValue) {
        // Only trigger action if value changed
        props.onChange(props.fieldName, selectedColor);
      }
    };
    /**
     * Bind function to document to detect when
     * user clicks outside color picker.
     */
    const handleClick = (event: any) => {
      if (
        pickerContainer.current &&
        !pickerContainer.current.contains(event.target)
      ) {
        hideColorPickerAndSubmit();
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => {
      document.removeEventListener('mousedown', handleClick);
    };
  }, [selectedColor, props]);

  const tooltip = !props.hideTooltip ? (
    <Tooltip id="redeployment-status">
      <WrappedMessage messages={props.messages} id={`${props.fieldName}Help`} />
    </Tooltip>
  ) : null;

  const fieldValue = () => {
    if (props.initialValue !== undefined) {
      return props.initialValue;
    }
    return 'Not set';
  };

  return (
    <FormGroup className="color-input">
      <FormLabel>
        <WrappedMessage id={genericFieldName} messages={props.messages} />
      </FormLabel>
      <Row className="align-items-center">
        <div className="d-flex align-items-center color-input-field">
          <FormControl
            className="input-field-color"
            name={props.fieldName}
            value={fieldValue()}
            disabled={props.loading}
            onClick={toggleColorPicker}
            readOnly
          />

          <div
            className="input-field-preview"
            style={{
              backgroundColor: props.initialValue
            }}
          />
        </div>

        {tooltip ? (
          <OverlayTrigger placement="right" overlay={tooltip}>
            <div className="info-icon">
              <i className="fas fa-info-circle" />
            </div>
          </OverlayTrigger>
        ) : (
          <button
            className="reset-value padded flex-grow"
            type="button"
            onClick={resetColor}
          >
            <WrappedMessage id="reset" messages={internalMessages} />
          </button>
        )}
      </Row>

      {tooltip ? (
        <p>
          <button className="reset-value" type="button" onClick={resetColor}>
            <WrappedMessage id="reset" messages={internalMessages} />
          </button>
        </p>
      ) : null}

      {colorPicker ? (
        <div ref={pickerContainer} className="input-color-picker">
          <SketchPicker
            color={selectedColor}
            onChangeComplete={color => {
              setColor(color.hex);
            }}
          />
        </div>
      ) : null}
    </FormGroup>
  );
};
