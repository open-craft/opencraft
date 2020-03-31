import * as React from 'react';
import './styles.scss';
import { CustomizableButton } from 'console/components';
import { CollapseEditArea, ColorInputField, ToggleSwitch } from 'ui/components';
import { InstanceSettingsModel } from 'console/models';
import { Col, Container, OverlayTrigger, Row, Tooltip } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import { ThemeSchema } from 'ocim-client';
import messages from './displayMessages';

interface ButtonCustomizationPageProps {
  buttonName: string;
  externalMessages: any;
  onChangeColor: Function;
  loading: Array<keyof InstanceSettingsModel | 'deployment'>;
  themeData: ThemeSchema;
  initialExpanded?: boolean;
  deploymentToggle?: boolean;
}

export const ButtonCustomizationPage: React.FC<ButtonCustomizationPageProps> = (
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

  const allStylesDefined = Object.values(styles)
    .map(category =>
      category.every(style => themeData[style as keyof typeof themeData])
    )
    .every(category => category);
  const switchTooltip = (
    <Tooltip id="button-tooltip">
      <WrappedMessage messages={messages} id="switchTooltipMessage" />
    </Tooltip>
  );
  const switchToggle = (
    <ToggleSwitch
      fieldName={`customize${props.buttonName}Btn`}
      initialValue={
        themeData[
          `customize${props.buttonName}Btn` as keyof typeof themeData
        ] as boolean
      }
      onChange={props.onChangeColor}
      disabled={!allStylesDefined}
    />
  );

  return (
    <div className="button-customization-page">
      <Row>
        <Col md={10}>
          <p className="button-name">
            <WrappedMessage
              messages={props.externalMessages}
              id={buttonFullName}
            />
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
          </p>
        </Col>
        <Col md={2}>
          <CustomizableButton
            initialTextColor={
              themeData[
                `btn${props.buttonName}Color` as keyof typeof themeData
              ] as string
            }
            initialBackgroundColor={
              themeData[
                `btn${props.buttonName}Bg` as keyof typeof themeData
              ] as string
            }
            initialBorderColor={
              themeData[
                `btn${props.buttonName}BorderColor` as keyof typeof themeData
              ] as string
            }
            initialHoverTextColor={
              themeData[
                `btn${props.buttonName}HoverColor` as keyof typeof themeData
              ] as string
            }
            initialHoverBackgroundColor={
              themeData[
                `btn${props.buttonName}HoverBg` as keyof typeof themeData
              ] as string
            }
            initialHoverBorderColor={
              themeData[
                `btn${props.buttonName}HoverBorderColor` as keyof typeof themeData
              ] as string
            }
          />
        </Col>
      </Row>

      <CollapseEditArea initialExpanded={props.initialExpanded || false}>
        <Container className="theme-button-customization-container">
          {Object.entries(styles).map(([category, fields]) => (
            <div key={category}>
              <Row>
                <p className="style-name">
                  <WrappedMessage messages={messages} id={category} />
                </p>
              </Row>
              <Row>
                {fields.map(field => (
                  <Col key={field}>
                    <ColorInputField
                      key={field}
                      fieldName={field}
                      genericFieldName={field.replace(props.buttonName, '')}
                      initialValue={
                        themeData[field as keyof typeof themeData] as string
                      }
                      onChange={props.onChangeColor}
                      messages={messages}
                      loading={loading.includes('draftThemeConfig')}
                      hideTooltip
                    />
                  </Col>
                ))}
              </Row>
            </div>
          ))}
        </Container>
      </CollapseEditArea>
    </div>
  );
};
