import * as React from 'react';
import { Button, FormControl, InputGroup, Spinner } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import { INTERNAL_DOMAIN_NAME } from 'global/constants';
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
          isInvalid={!!props.error}
        />
        {props.internalDomain && (
          <InputGroup.Append>
            <InputGroup.Text>{INTERNAL_DOMAIN_NAME}</InputGroup.Text>
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
            {props.loading && (
              <Spinner animation="border" size="sm" className="spinner" />
            )}
            <WrappedMessage messages={messages} id="checkAvailability" />
          </Button>
        </InputGroup.Append>
        {props.error && (
          <FormControl.Feedback type="invalid">
            {props.error}
          </FormControl.Feedback>
        )}
      </InputGroup>
    </div>
  );
};
