import * as React from 'react';
// import messages from './displayMessages';
import './styles.scss';

interface CustomizableLinkProps {
  children?: React.ReactNode;
  linkColor?: string;
  borderBottomColor?: string;
  borderBottomHoverColor?: string;
  active?: boolean;
  noHover?: boolean;
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
    borderBottomColor: props.borderBottomHoverColor
      ? props.borderBottomHoverColor
      : undefined
  });

  function toggleHover() {
    if (!props.noHover) {
      setHover(!hover);
    }
  }

  React.useEffect(() => {
    setStyle({
      color: props.linkColor,
      borderBottomColor: props.active ? props.borderBottomColor : undefined
    });
  }, [props.linkColor, props.borderBottomColor, props.active]);
  React.useEffect(() => {
    setHoverStyle({
      color: props.linkColor,
      borderBottomColor: props.borderBottomHoverColor
        ? props.borderBottomHoverColor
        : undefined
    });
  }, [props.linkColor, props.borderBottomHoverColor]);

  const className =
    `customizable-link` +
    `${props.active ? ' active' : ''}` +
    `${props.noHover ? ' noHover' : ''}`;

  return (
    <button
      type="button"
      className={className}
      style={hover ? hoverStyle : style}
      onMouseEnter={toggleHover}
      onMouseLeave={toggleHover}
    >
      {props.children}
    </button>
  );
};
