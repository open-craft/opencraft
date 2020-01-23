import * as React from 'react';
import { Jumbotron } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import { INTERNAL_DOMAIN_NAME } from 'global/constants';
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

  if (props.domainIsExternal) {
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
        <p>
          {props.domain}
          {!props.domainIsExternal && <span>{INTERNAL_DOMAIN_NAME}</span>}
        </p>
      </div>
      <p>
        <WrappedMessage id="secureDomainNow" messages={messages} />
      </p>
    </Jumbotron>
  );
};
