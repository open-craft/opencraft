import * as React from 'react';
import { FormControl, FormGroup, FormLabel } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import './styles.scss';

interface InputFieldProps {
  fieldName: string;
  helpMessageId?: string;
  value?: string;
  onChange?: React.ChangeEventHandler<HTMLInputElement>;
  onBlur?: React.FocusEventHandler<HTMLInputElement>;
  error?: string;
  messages: any;
  type?: string;
  isValid?: boolean;
  loading?: boolean;
  reset?: Function;
  autoComplete?: string;
}

export const TextInputField: React.FC<InputFieldProps> = (
  props: InputFieldProps
) => {
  let helpMessage;
  const helpMessageId = props.helpMessageId || `${props.fieldName}Help`;
  const hasHelpMessage = helpMessageId in props.messages;
  if (hasHelpMessage) {
    helpMessage = (
      <WrappedMessage id={helpMessageId} messages={props.messages} />
    );
  }

  return (
    <TextInputField2
      label={<WrappedMessage id={props.fieldName} messages={props.messages} />}
      helpMessage={helpMessage}
      {...props}
    />
  );
};

interface TextInputField2Props {
  autoComplete?: string;
  error?: string;
  fieldName: string;
  helpMessage?: React.ReactNode;
  isValid?: boolean;
  label: React.ReactNode;
  loading?: boolean;
  onBlur?: React.FocusEventHandler<HTMLInputElement>;
  onChange?: React.ChangeEventHandler<HTMLInputElement>;
  reset?: Function;
  type?: string;
  value?: string;
}

export const TextInputField2: React.FC<TextInputField2Props> = (
  props: TextInputField2Props
) => {
  return (
    <div className="text-input-container">
      <FormGroup>
        <FormLabel>{props.label}</FormLabel>
        <FormControl
          name={props.fieldName}
          value={props.value}
          disabled={props.loading}
          onChange={props.onChange}
          onBlur={props.onBlur}
          type={props.type}
          isInvalid={!!props.error}
          isValid={props.isValid}
          autoComplete={props.autoComplete}
        />
        {props.error && (
          <FormControl.Feedback type="invalid">
            {props.error}
          </FormControl.Feedback>
        )}
        {props.helpMessage && <p>{props.helpMessage}</p>}
      </FormGroup>

      {props.reset !== undefined && (
        <p>
          <button
            className="reset-default"
            type="button"
            onClick={() => {
              // Using `!` because we know this will never be called
              // if props.reset is undefined (this component won't be
              // rendered).
              props.reset!();
            }}
          >
            Reset
          </button>
        </p>
      )}
    </div>
  );
};
