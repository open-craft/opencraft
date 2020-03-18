import * as React from 'react';
import messages from './displayMessages';
import './styles.scss';
import { WrappedMessage } from '../../../utils/intl';

interface CustomizableButtonProps {
  children?: React.ReactNode;
  initialBackgroundColor?: string;
  initialTextColor?: string;
  initialBorderColor?: string;
  initialHoverBackgroundColor?: string;
  initialHoverTextColor?: string;
  initialHoverBorderColor?: string;
  background?: string;
  borderColor?: string;
}

export const CustomizableButton: React.FC<CustomizableButtonProps> = (
  props: CustomizableButtonProps
) => {
  const [hover, setHover] = React.useState(false);
  const [style, setStyle] = React.useState({
    background: props.initialBackgroundColor,
    color: props.initialTextColor,
    borderColor: props.initialBorderColor
  });
  const [hoverStyle, setHoverStyle] = React.useState({
    background: props.initialHoverBackgroundColor,
    color: props.initialHoverTextColor,
    borderColor: props.initialHoverBorderColor
  });

  function toggleHover() {
    setHover(!hover);
  }

  React.useEffect(() => {
    setStyle({
      background: props.initialBackgroundColor,
      color: props.initialTextColor,
      borderColor: props.initialBorderColor
    });
  }, [
    props.initialTextColor,
    props.initialBackgroundColor,
    props.initialBorderColor
  ]);

  React.useEffect(() => {
    setHoverStyle({
      background: props.initialHoverBackgroundColor,
      color: props.initialHoverTextColor,
      borderColor: props.initialHoverBorderColor
    });
  }, [
    props.initialHoverTextColor,
    props.initialHoverBackgroundColor,
    props.initialHoverBorderColor
  ]);

  return (
    <button
      type="button"
      className="customizable-button"
      onMouseEnter={toggleHover}
      onMouseLeave={toggleHover}
      style={hover ? hoverStyle : style}
    >
      {props.children || (
        <WrappedMessage messages={messages} id="exampleMessage" />
      )}
    </button>
  );
};
