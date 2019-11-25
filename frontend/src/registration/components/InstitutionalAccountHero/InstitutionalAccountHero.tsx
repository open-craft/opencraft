import * as React from 'react';
import {
  REACT_APP_CONTACT_US_LINK,
  REACT_APP_ENTERPRISE_COMPARISON_LINK
} from 'global/constants';
import { Button } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';

import messages from './displayMessages';

import './styles.scss';

export const InstitutionalAccountHero: React.FC = () => (
  <div className="hero-container">
    <div className="hero-div">
      <h2>
        <WrappedMessage messages={messages} id="institutionalAccountTitle" />
      </h2>
      <p>
        <WrappedMessage messages={messages} id="institutionalAccountText" />
      </p>
      <div className="institutional-button-container">
        <Button
          variant="outline-primary"
          size="lg"
          onClick={() => {
            window.location.href = REACT_APP_CONTACT_US_LINK;
          }}
        >
          <WrappedMessage messages={messages} id="contactUsButton" />
        </Button>
        <Button
          variant="secondary"
          size="lg"
          onClick={() => {
            window.location.href = REACT_APP_ENTERPRISE_COMPARISON_LINK;
          }}
        >
          <WrappedMessage messages={messages} id="findOutMoreButton" />
        </Button>
      </div>
    </div>
  </div>
);
