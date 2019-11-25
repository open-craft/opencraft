import * as React from 'react';
import { Jumbotron } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import iconCheck from 'assets/circle-check.png';
import messages from './displayMessages';
import './styles.scss';

interface DomainProps {
  domain: string;
  domainIsExternal: boolean;
}

export const DomainSuccessJumbotron: React.FC<DomainProps> = (
  props: DomainProps
) => {
  let domainStatusText: string;

  if (props.domainIsExternal === true) {
    domainStatusText = 'domainIsConnected';
  } else {
    domainStatusText = 'domainIsAvailable';
  }

  return (
    <Jumbotron className="domain-available">
      <img src={iconCheck} alt="" />
      <h2>
        <WrappedMessage id={domainStatusText} messages={messages} />
      </h2>
      <div className="domain-name">
        <p>{props.domain}</p>
      </div>
      <p>
        <WrappedMessage id="secureDomainNow" messages={messages} />
      </p>
    </Jumbotron>
  );
};
