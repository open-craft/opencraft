import * as React from 'react';
import { FormControl, FormGroup, FormLabel } from 'react-bootstrap';
import { BlockPicker } from 'react-color';
import { WrappedMessage } from 'utils/intl';
import './styles.scss';

interface ColorInputFieldProps {
  fieldName: string;
  value?: string;
  onChange?: any;
  onBlur?: any;
  error?: string;
  messages: any;
  isValid?: boolean;
  loading?: boolean;
}

export const ColorInputField: React.SFC<ColorInputFieldProps> = (
  props: ColorInputFieldProps
) => {
  const hasHelpMessage = `${props.fieldName}Help` in props.messages;
  const [colorPicker, setColorPicker] = React.useState(false);
  const [selectedColor, setColor] = React.useState(props.value);

  const showColorPicker = () => {
    setColorPicker(true);
  };

  const resetColor = () => {
    setColor(props.value);
    props.onBlur();
  };

  const hideColorPickerAndSubmit = () => {
    setColorPicker(false);

    if (selectedColor !== props.value) {
      // Only trigger action if value changed
      props.onChange(props.fieldName, selectedColor);
    }
  };

  return (
    <FormGroup>
      <FormLabel>
        <WrappedMessage id={props.fieldName} messages={props.messages} />
      </FormLabel>
      <FormControl
        className="input-field-color"
        name={props.fieldName}
        value={selectedColor}
        disabled={props.loading}
        onFocus={showColorPicker}
        isValid={props.isValid}
        style={{ color: selectedColor }}
        readOnly
      />
      {hasHelpMessage && (
        <WrappedMessage
          id={`${props.fieldName}Help`}
          messages={props.messages}
        />
      )}
      <p>
        <button onClick={resetColor}>
          <WrappedMessage id="reset" messages={props.messages} />
        </button>
      </p>

      {colorPicker ? (
        <div
          className="input-color-picker"
          onBlur={hideColorPickerAndSubmit}
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