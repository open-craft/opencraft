import * as React from 'react';
// import messages from './displayMessages';
import './styles.scss';

interface CustomizableLinkProps {
  children?: React.ReactNode;
  linkColor?: string;
  borderBottomColor?: string;
  borderBottomHoverColor?: string;
  active?: boolean
}

export const CustomizableLink: React.FC<CustomizableLinkProps> = (
  props: CustomizableLinkProps
) => {
  const [hover, setHover] = React.useState(false);
  const [style, setStyle] = React.useState({
    color: props.linkColor,
    borderBottomColor: props.active ? props.borderBottomColor : undefined
  });
  const [hoverStyle, setHoverStyle] = React.useState({
    color: props.linkColor,
    borderBottomColor: props.borderBottomHoverColor ? props.borderBottomHoverColor : undefined
  });

  function toggleHover() {
    setHover(!hover);
  }

  React.useEffect(() => {
    setStyle({
      color: props.linkColor,
      borderBottomColor: props.active ? props.borderBottomColor : undefined
    });
  }, [props.linkColor, props.borderBottomColor]);
  React.useEffect(() => {
    setHoverStyle({
      color: props.linkColor,
      borderBottomColor: props.borderBottomHoverColor ? props.borderBottomHoverColor : undefined
    });
  }, [props.linkColor, props.borderBottomHoverColor]);

  return (
    <button
      type='button'
      className={`customizable-link ${props.active ? 'active': ''}`}
      style={hover ? hoverStyle : style}
      onMouseEnter={toggleHover}
      onMouseLeave={toggleHover}
    >
      {props.children}
    </button>
  );
};
