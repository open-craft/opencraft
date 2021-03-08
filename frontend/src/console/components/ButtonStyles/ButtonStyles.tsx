import * as React from 'react';
import { InstanceSettingsModel } from 'console/models';
import { ThemeSchema } from 'ocim-client';
import { Col, Container, Row } from 'react-bootstrap';
import { CollapseEditArea, ColorInputField } from 'ui/components';
import { WrappedMessage } from 'utils/intl';
import messages from './displayMessages';
import './styles.scss';

interface ButtonStylesProp {
  onChangeColor: Function;
  buttonName: string;
  themeData: ThemeSchema;
  initialExpanded?: boolean;
  loading: Array<keyof InstanceSettingsModel | 'deployment'>;
}

export const ButtonStyles: React.FC<ButtonStylesProp> = (
  props: ButtonStylesProp
) => {
  const { themeData } = props;
  const { loading } = props;

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

  return (
    <CollapseEditArea initialExpanded={props.initialExpanded || false}>
      <Container className="theme-button-customization-container">
        {Object.entries(styles).map(([category, fields]) => (
          <div key={category}>
            <Row>
              <p className="style-name">
                <WrappedMessage messages={messages} id={category} />
              </p>
            </Row>
            <Row className="color-picker-group">
              {fields.map(field => (
                <Col md={4} xs={12} key={field} className="color-picker-item">
                  <ColorInputField
                    key={field}
                    fieldName={field}
                    genericFieldName={field.replace(props.buttonName, '')}
                    initialValue={
                      (themeData[field as keyof typeof themeData] as string) ||
                      ''
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
  );
};
