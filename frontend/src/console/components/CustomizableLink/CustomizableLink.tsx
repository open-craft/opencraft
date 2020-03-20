import * as React from 'react';
// import messages from './displayMessages';
import './styles.scss';

interface CustomizableLinkProps {
  children?: React.ReactNode;
  linkColor?: string;
  borderBottomColor?: string;
  borderBottomHoverColor?: string;
}

export const CustomizableLink: React.FC<CustomizableLinkProps> = (
  props: CustomizableLinkProps
) => {
  const [hover, setHover] = React.useState(false);
  const [style, setStyle] = React.useState({
    color: props.linkColor,
    borderBottom: props.borderBottomColor
      ? `4px solid ${props.borderBottomColor}`
      : ''
  });
  const [hoverStyle, setHoverStyle] = React.useState({
    color: props.linkColor,
    borderBottom: props.borderBottomHoverColor
      ? `4px solid ${props.borderBottomHoverColor}`
      : ''
  });

  function toggleHover() {
    setHover(!hover);
  }

  React.useEffect(() => {
    setStyle({
      color: props.linkColor,
      borderBottom: props.borderBottomColor
        ? `4px solid ${props.borderBottomColor}`
        : ''
    });
  }, [props.linkColor, props.borderBottomColor]);
  React.useEffect(() => {
    setHoverStyle({
      color: props.linkColor,
      borderBottom: props.borderBottomHoverColor
        ? `4px solid ${props.borderBottomHoverColor}`
        : ''
    });
  }, [props.linkColor, props.borderBottomHoverColor]);

  return (
    <a
      className="customizable-link"
      href="#"
      style={hover ? hoverStyle : style}
      onMouseEnter={toggleHover}
      onMouseLeave={toggleHover}
    >
      {props.children}
    </a>
  );
};
