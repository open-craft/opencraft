import * as React from 'react';
import messages from './displayMessages';
import './styles.scss';
import {Button} from "react-bootstrap";
import {WrappedMessage} from "../../../utils/intl";

interface CustomizableButtonProps {
  children?: React.ReactNode;
  initialBackgroundColor?: string;
  initialTextColor?: string;
  initialBorderBlockColor?: string;
  initialHoverBackgroundColor?: string;
  initialHoverTextColor?: string;
  initialHoverBorderBlockColor?: string;
  background?: string;
  borderBlockColor?: string;
}

export const CustomizableButton: React.FC<CustomizableButtonProps> = (props: CustomizableButtonProps) => {
  const [hover, setHover] = React.useState(false);
  const [style, setStyle] = React.useState({
    background: props.initialBackgroundColor,
    color: props.initialTextColor,
    borderBlockColor: props.initialBorderBlockColor
  });
  const [hoverStyle, setHoverStyle] = React.useState({
    background: props.initialHoverBackgroundColor,
    color: props.initialHoverTextColor,
    borderBlockColor: props.initialHoverBorderBlockColor
  });

  function toggleHover() {
    setHover(!hover);
  }

  React.useEffect(() => {
    setStyle({
      background: props.initialBackgroundColor,
      color: props.initialTextColor,
      borderBlockColor: props.initialBorderBlockColor
    });
  }, [props.initialTextColor, props.initialBackgroundColor, props.initialBorderBlockColor]);

  React.useEffect(() => {
    setHoverStyle({
      background: props.initialHoverBackgroundColor,
      color: props.initialHoverTextColor,
      borderBlockColor: props.initialHoverBorderBlockColor
    });
  }, [props.initialHoverTextColor, props.initialHoverBackgroundColor, props.initialHoverBorderBlockColor]);

  return (
    <Button onMouseEnter={toggleHover} onMouseLeave={toggleHover} style={hover ? hoverStyle : style}>
      {props.children || <WrappedMessage messages={messages} id={`exampleMessage`}/>}
    </Button>
  );
};
