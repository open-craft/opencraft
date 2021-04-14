import * as React from 'react';
import { Collapse, Nav } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import messages from './displayMessages';
import './styles.scss';

interface PreviewDropdownProps {
  handleChange: Function;
}

export const PreviewDropdown: React.FC<PreviewDropdownProps> = (
  props: PreviewDropdownProps
) => {
  const [open, setOpen] = React.useState(false);
  const [selectedPreview, setSelectedPreview] = React.useState('dashboard');
  const updatePreview = (key: string) => {
    setSelectedPreview(key);
    setOpen(!open);
    props.handleChange(key);
  };
  const iconName = open ? 'fa-chevron-up' : 'fa-chevron-down';
  const children = () => {
    const toRender: JSX.Element[] = [];

    Object.entries(messages).forEach(([key, _]) =>
      toRender.push(
        <button
          onClick={() => updatePreview(key)}
          key={key}
          type="button"
          className="d-inline-block"
        >
          <p>
            <WrappedMessage messages={messages} id={key} />
          </p>
        </button>
      )
    );

    return <div>{toRender}</div>;
  };

  return (
    <div className="dropdown-container d-flex flex-column align-items-center">
      <Nav.Link onClick={() => setOpen(!open)}>
        <WrappedMessage messages={messages} id={selectedPreview} />
        <i className={`fas xs ${iconName}`} />
      </Nav.Link>
      <span className="fill-line" />
      <div className="dropdown-items align-items-center">
        <div className="content d-flex flex-column">
          <Collapse in={open}>{children()}</Collapse>
        </div>
      </div>
    </div>
  );
};
