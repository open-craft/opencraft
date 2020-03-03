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
  initialValue?: string;
  onChange?: any;
  error?: string;
  messages: any;
  loading?: boolean;
}

export const ColorInputField: React.SFC<ColorInputFieldProps> = (
  props: ColorInputFieldProps
) => {
  const [colorPicker, setColorPicker] = React.useState(false);
  const [selectedColor, setColor] = React.useState(props.initialValue);

  const showColorPicker = () => {
    setColorPicker(true);
  };

  const resetColor = () => {
    setColor(props.initialValue);
    props.onChange(props.fieldName, selectedColor);
  };

  const hideColorPickerAndSubmit = () => {
    setColorPicker(false);

    if (selectedColor !== props.initialValue) {
      // Only trigger action if value changed
      props.onChange(props.fieldName, selectedColor);
    }
  };

  const tooltip = (
    <Tooltip id="redeployment-status">
      <WrappedMessage messages={props.messages} id={`${props.fieldName}Help`} />
    </Tooltip>
  );

  return (
    <FormGroup>
      <FormLabel>
        <WrappedMessage id={props.fieldName} messages={props.messages} />
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

        <OverlayTrigger placement="right" overlay={tooltip}>
          <div className="info-icon">
            <i className="fas fa-info-circle" />
          </div>
        </OverlayTrigger>
      </Row>

      <p>
        <button className="reset-value" type="button" onClick={resetColor}>
          <WrappedMessage id="reset" messages={internalMessages} />
        </button>
      </p>

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
