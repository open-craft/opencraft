import * as React from 'react';
import { Button, FormControl, InputGroup, Spinner } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import messages from './displayMessages';
import './styles.scss';

interface Props {
  domainName: string;
  internalDomain: boolean;
  loading: boolean;
  error: string;
  handleDomainChange: Function;
  handleSubmitDomain: Function;
}

export const DomainInput: React.SFC<Props> = (props: Props) => {
  const isInvalid = !!props.error;
  return (
    <div className="domain-input-container">
      <div className="domain-label">
        <WrappedMessage messages={messages} id="typeDomainNameBelow" />
      </div>
      <InputGroup>
        <FormControl
          value={props.domainName}
          onChange={(event: any) => {
            props.handleDomainChange(event.target.value);
          }}
          isInvalid={isInvalid}
        />
        {props.internalDomain === true && (
          <InputGroup.Append>
            <InputGroup.Text>.opencraft.hosting</InputGroup.Text>
          </InputGroup.Append>
        )}
        <InputGroup.Append>
          <Button
            variant="primary"
            disabled={false || props.loading}
            onClick={(event: any) => {
              props.handleSubmitDomain();
            }}
          >
            {props.loading === true && (
              <Spinner animation="border" size="sm" className="spinner" />
            )}
            <WrappedMessage messages={messages} id="checkAvailability" />
          </Button>
        </InputGroup.Append>
        {isInvalid && (
          <FormControl.Feedback type="invalid">
            {props.error}
          </FormControl.Feedback>
        )}
      </InputGroup>
    </div>
  );
};
