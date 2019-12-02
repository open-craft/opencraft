import * as React from 'react';
import './styles.scss';

import { Button } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import messages from './displayMessages';

interface Props {
  showBackButton: boolean;
  showNextButton: boolean;
  disableNextButton: boolean;
  handleNextClick?: Function;
  handleBackClick?: Function;
}

export const RegistrationNavButtons: React.SFC<Props> = (props: Props) => {
  return (
    <div className="registration-nav">
      <Button className="float-left" variant="outline-primary" size="lg">
        <WrappedMessage messages={messages} id="back" />
      </Button>
      <Button
        className="float-right"
        variant="primary"
        size="lg"
        disabled={props.disableNextButton}
      >
        <WrappedMessage messages={messages} id="Next" />
      </Button>
    </div>
  );
};
