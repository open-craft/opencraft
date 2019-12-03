import * as React from 'react';
import './styles.scss';

import { Button, Spinner } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import messages from './displayMessages';

interface Props {
  loading: boolean;
  showBackButton: boolean;
  showNextButton: boolean;
  disableNextButton: boolean;
  handleNextClick: Function;
  handleBackClick: Function;
}

export const RegistrationNavButtons: React.SFC<Props> = (props: Props) => {
  return (
    <div className="registration-nav">
      <Button
        className="float-left"
        variant="outline-primary"
        size="lg"
        onClick={() => {
          props.handleBackClick();
        }}
      >
        <WrappedMessage messages={messages} id="back" />
      </Button>
      <Button
        className="float-right loading"
        variant="primary"
        size="lg"
        disabled={props.disableNextButton || props.loading}
        data-loading-text="</i> Processing Order"
        onClick={() => {
          props.handleNextClick();
        }}
      >
        {props.loading === true && (
          <Spinner animation="border" size="sm" className="spinner" />
        )}
        <WrappedMessage messages={messages} id="Next" />
      </Button>
    </div>
  );
};
