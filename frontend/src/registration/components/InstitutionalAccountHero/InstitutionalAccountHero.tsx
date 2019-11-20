import * as React from 'react';
import { Button } from "react-bootstrap";
import { WrappedMessage } from "utils/intl";

import messages from './displayMessages';

import './styles.scss';

export const InstitutionalAccountHero: React.FC = () => (
    <div className="hero-container">
        <div className="hero-div">
            <h2>
              <WrappedMessage messages={messages} id="institutionalAccountTitle"/>
            </h2>
            <p>
              <WrappedMessage messages={messages} id="institutionalAccountText"/>
            </p>
            <div className="institutional-button-container">
              <Button variant="outline-primary" size="lg">
                <WrappedMessage messages={messages} id="contactUsButton"/>
              </Button>
              <Button variant="secondary" size="lg">
                <WrappedMessage messages={messages} id="findOutMoreButton"/>
              </Button>
            </div>
        </div>
    </div>
);
