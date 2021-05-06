import * as React from 'react';
import { InstanceSettingsModel } from 'console/models';
import { Form, OverlayTrigger, Tooltip } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import { ThemeSchema } from 'ocim-client';
import messages from './displayMessages';
import './styles.scss';
import { ButtonStyles } from '../ButtonStyles';

interface ButtonCustomizationPageProps {
  buttonName: string;
  externalMessages: any;
  onChangeColor: Function;
  loading: Array<keyof InstanceSettingsModel | 'deployment'>;
  themeData: ThemeSchema;
  initialExpanded?: boolean;
  deploymentToggle?: boolean;
}

export const ButtonCustomizationComponent: React.FC<ButtonCustomizationPageProps> = (
  props: ButtonCustomizationPageProps
) => {
  const { themeData } = props;
  const { loading } = props;
  const buttonFullName = `theme${props.buttonName}Button`;

  const tooltip = (
    <Tooltip id="button-tooltip">
      <WrappedMessage
        messages={props.externalMessages}
        id={`${buttonFullName}Help`}
      />
    </Tooltip>
  );

  const styles = {
    activeStyles: [
      `btn${props.buttonName}Bg`,
      `btn${props.buttonName}Color`,
      `btn${props.buttonName}BorderColor`
    ],
    hoverStyles: [
      `btn${props.buttonName}HoverBg`,
      `btn${props.buttonName}HoverColor`,
      `btn${props.buttonName}HoverBorderColor`
    ]
  };

  let customizationProp = `customize${props.buttonName}Btn`;
  if (props.buttonName === 'Logistration') {
    // Logistration toggle doesn't follow the common naming convention, hence setting it explicitly.
    // See SE-2955 for discussion.
    customizationProp = `customizeLogistrationActionBtn`;
  }

  const allStylesDefined = Object.values(styles)
    .map(category =>
      category.every(style => themeData[style as keyof typeof themeData])
    )
    .every(category => category);
  const customizationEnabled =
    (themeData[customizationProp as keyof typeof themeData] as
      | boolean
      | undefined) || false;

  const switchTooltip = (
    <Tooltip id="button-tooltip">
      <WrappedMessage messages={messages} id="switchTooltipMessage" />
    </Tooltip>
  );
  const switchToggle = (
    <Form.Check
      id={`toggle-${props.buttonName}`}
      type="switch"
      label=""
      checked={customizationEnabled}
      onChange={() => {
        props.onChangeColor(customizationProp, !customizationEnabled);
      }}
      disabled={!allStylesDefined}
    />
  );

  return (
    <div className="button-customization-container">
      <div className="button-customization-name">
        <WrappedMessage messages={props.externalMessages} id={buttonFullName} />
        <OverlayTrigger placement="right" overlay={tooltip}>
          <span className="info-icon">
            <i className="fas fa-info-circle" />
          </span>
        </OverlayTrigger>
        {props.deploymentToggle &&
          (!allStylesDefined ? (
            <OverlayTrigger placement="right" overlay={switchTooltip}>
              <span className="info-icon">{switchToggle}</span>
            </OverlayTrigger>
          ) : (
            switchToggle
          ))}
      </div>
      <div className="button-customization-color-container">
        <ButtonStyles
          buttonName={props.buttonName}
          onChangeColor={props.onChangeColor}
          themeData={themeData}
          loading={loading}
          initialExpanded={props.initialExpanded || false}
        />
      </div>
    </div>
  );
};
