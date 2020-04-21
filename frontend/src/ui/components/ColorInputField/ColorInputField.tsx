import * as React from 'react';
import {
  FormControl,
  FormGroup,
  FormLabel,
  Row,
  Tooltip,
  OverlayTrigger
} from 'react-bootstrap';

import { BlockPicker } from 'react-color';
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

export const ColorInputField: React.SFC<ColorInputFieldProps> = (
  props: ColorInputFieldProps
) => {
  const [colorPicker, setColorPicker] = React.useState(false);
  const [selectedColor, setColor] = React.useState(props.initialValue);

  // Get name that can be used with generic displayMessages.
  const genericFieldName = props.genericFieldName || props.fieldName;

  // Ensure the correct color is shown if props are updated
  React.useEffect(() => {
    setColor(props.initialValue);
  }, [props.initialValue]);

  const showColorPicker = () => {
    setColorPicker(true);
  };

  const resetColor = () => {
    // This will reset the field value to the default theme value
    // TODO: this will need to be updated when the Theme configuration endpoint
    // get updated to improve consistency
    props.onChange(props.fieldName, '');
  };

  const hideColorPickerAndSubmit = () => {
    setColorPicker(false);

    if (selectedColor !== props.initialValue) {
      // Only trigger action if value changed
      props.onChange(props.fieldName, selectedColor);
    }
  };

  const tooltip = !props.hideTooltip ? (
    <Tooltip id="redeployment-status">
      <WrappedMessage messages={props.messages} id={`${props.fieldName}Help`} />
    </Tooltip>
  ) : null;

  return (
    <FormGroup>
      <FormLabel>
        <WrappedMessage id={genericFieldName} messages={props.messages} />
      </FormLabel>
      <Row>
        <FormControl
          className="input-field-color"
          name={props.fieldName}
          value={selectedColor}
          disabled={props.loading}
          onFocus={showColorPicker}
          style={{ color: selectedColor }}
          readOnly
        />

        {tooltip ? (
          <OverlayTrigger placement="right" overlay={tooltip}>
            <div className="info-icon">
              <i className="fas fa-info-circle" />
            </div>
          </OverlayTrigger>
        ) : (
          <button
            className="reset-value padded"
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
        <div
          className="input-color-picker"
          onBlur={hideColorPickerAndSubmit}
          role="button"
          tabIndex={0}
          onKeyDown={e => {
            if (e.key === 'Enter') {
              hideColorPickerAndSubmit();
            }
          }}
        >
          <BlockPicker
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
