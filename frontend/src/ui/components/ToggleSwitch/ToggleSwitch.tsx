import * as React from 'react';
import './styles.scss';

interface ToggleSwitchProps {
  fieldName: string;
  initialValue?: boolean;
  onChange?: any;
  error?: string;
  disabled?: boolean;
}

export const ToggleSwitch: React.SFC<ToggleSwitchProps> = (
  props: ToggleSwitchProps
) => {
  const [value, setValue] = React.useState(props.initialValue);

  // Ensure the correct value is shown if props are updated.
  React.useEffect(() => {
    setValue(props.initialValue || false);
  }, [props.initialValue]);

  const onChange = () => {
    props.onChange(props.fieldName, !value);
  };

  return (
    <label className="switch">
      <input
        type="checkbox"
        checked={value}
        onChange={onChange}
        disabled={props.disabled}
      />
      <span className="slider round" />
    </label>
  );
};
