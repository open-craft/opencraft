import * as React from 'react';
import { FormControl, FormGroup, FormLabel } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import './styles.scss';

interface InputFieldProps {
  fieldName: string;
  value?: string;
  onChange?: any;
  onBlur?: any;
  error?: string;
  messages: any;
  type?: string;
  isValid?: boolean;
  loading?: boolean;
}

export const TextInputField: React.SFC<InputFieldProps> = (
  props: InputFieldProps
) => {
  const hasHelpMessage = `${props.fieldName}Help` in props.messages;

  return (
    <FormGroup>
      <FormLabel>
        <WrappedMessage id={props.fieldName} messages={props.messages} />
      </FormLabel>
      <FormControl
        name={props.fieldName}
        value={props.value}
        disabled={props.loading}
        onChange={props.onChange}
        onBlur={props.onBlur}
        type={props.type}
        isInvalid={!!props.error}
        isValid={props.isValid}
      />
      {props.error && (
        <FormControl.Feedback type="invalid">
          {props.error}
        </FormControl.Feedback>
      )}
      <p>
        {hasHelpMessage && (
          <WrappedMessage
            id={`${props.fieldName}Help`}
            messages={props.messages}
          />
        )}
      </p>
    </FormGroup>
  );
};
