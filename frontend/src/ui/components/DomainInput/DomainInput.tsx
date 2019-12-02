import * as React from 'react';
import { Button, FormControl, InputGroup } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import messages from './displayMessages';
import './styles.scss';

interface Props {
  domainName: string;
  internalDomain: boolean;
  handleDomainChange: Function;
  handleSubmitDomain: Function;
}

export const DomainInput: React.SFC<Props> = (props: Props) => {
  return (
    <div>
      <div className="domain-label">
        <WrappedMessage messages={messages} id="typeDomainNameBelow" />
      </div>
      <InputGroup>
        <FormControl
          value={props.domainName}
          onChange={(event: any) => {
            props.handleDomainChange(event.target.value);
          }}
        />
        {props.internalDomain === true && (
          <InputGroup.Append>
            <InputGroup.Text className="">.opencraft.hosting</InputGroup.Text>
          </InputGroup.Append>
        )}
        <InputGroup.Append>
          <Button
            variant="secondary"
            onClick={(event: any) => {
              props.handleSubmitDomain();
            }}
          >
            <WrappedMessage messages={messages} id="checkAvailability" />
          </Button>
        </InputGroup.Append>
      </InputGroup>
    </div>
  );
};
