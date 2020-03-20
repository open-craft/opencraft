import * as React from 'react';
import { Collapse, Nav } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import messages from './displayMessages';
import './styles.scss';

interface CollapseEditAreaProps {
  children: React.ReactNode;
  initialExpanded?: boolean;
}

export const CollapseEditArea: React.FC<CollapseEditAreaProps> = (
  props: CollapseEditAreaProps
) => {
  const [open, setOpen] = React.useState(props.initialExpanded || false);

  return (
    <div className="collapsible-edit-area">
      <div className="edit-collapse">
        <Nav.Link onClick={() => setOpen(!open)}>
          <WrappedMessage messages={messages} id="edit" />
          {open ? (
            <i className="fas xs fa-chevron-up" />
          ) : (
            <i className="fas xs fa-chevron-down" />
          )}
        </Nav.Link>
        <span className="fill-line" />
      </div>

      <Collapse in={open}>
        <div className="content">{props.children}</div>
      </Collapse>
    </div>
  );
};
