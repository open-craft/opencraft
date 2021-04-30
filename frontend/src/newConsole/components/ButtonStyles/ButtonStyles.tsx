import * as React from 'react';
import { InstanceSettingsModel } from 'console/models';
import { ThemeSchema } from 'ocim-client';
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
      {Object.entries(styles).map(([category, fields]) => (
        <div className="button-category" key={category}>
          <div>
            <p className="button-state-name">
              <WrappedMessage messages={messages} id={category} />
            </p>
          </div>
          <div>
            {fields.map(field => (
              <div key={field}>
                <ColorInputField
                  key={field}
                  fieldName={field}
                  genericFieldName={field.replace(props.buttonName, '')}
                  initialValue={
                    (themeData[field as keyof typeof themeData] as string) || ''
                  }
                  onChange={props.onChangeColor}
                  messages={messages}
                  loading={loading.includes('draftThemeConfig')}
                  hideTooltip
                />
              </div>
            ))}
          </div>
        </div>
      ))}
    </CollapseEditArea>
  );
};
