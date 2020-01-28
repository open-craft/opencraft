import * as React from 'react';
// import messages from './displayMessages';
import { Button, Tooltip, OverlayTrigger } from 'react-bootstrap';
import './styles.scss';

export const RedeploymentToolbar: React.FC = () => {
  const tooltip = (
    <Tooltip id="redeployment-status">
      Your instance is up-to-date with the latest settings.
    </Tooltip>
  );

  return (
    <div className="d-flex justify-content-center align-middle redeployment-toolbar">
      <div className="redeployment-nav">
        <OverlayTrigger placement="right" overlay={tooltip}>
          <div className="status-pill">
            <span className="dot" />
            <span className="text">Status: Up to date</span>
          </div>
        </OverlayTrigger>
        <Button
          className="float-right loading"
          disabled
          variant="primary"
          size="lg"
        >
          Deploy (10 updates)
        </Button>
      </div>
    </div>
  );
};
