import * as React from 'react';
import './styles.scss';
import {
  ButtonCustomizationPage,
  ConsolePage,
  ConsolePageCustomizationContainer
} from 'console/components';
import { InstancesModel } from 'console/models';
import { connect } from 'react-redux';
import { RootState } from 'global/state';
import { updateThemeFieldValue } from 'console/actions';
import messages from './displayMessages';

interface State {}

interface ActionProps {
  updateThemeFieldValue: Function;
}

interface StateProps extends InstancesModel {}

interface Props extends StateProps, ActionProps {}

export class ThemeButtonsComponent extends React.PureComponent<Props, State> {
  private onChangeColor = (fieldName: string, newColor: string) => {
    const instance = this.props.activeInstance;

    if (instance.data) {
      this.props.updateThemeFieldValue(instance.data.id, fieldName, newColor);
    }
  };

  public render() {
    const instance = this.props.activeInstance;
    let themeData;

    if (instance.data && instance.data.draftThemeConfig) {
      themeData = instance.data.draftThemeConfig;
    }

    return (
      <ConsolePage contentLoading={this.props.loading}>
        {themeData && themeData.version === 1 && (
          <div className="theme-buttons-container">
            <ConsolePageCustomizationContainer>
              <ButtonCustomizationPage
                buttonName="Primary"
                externalMessages={messages}
                onChangeColor={this.onChangeColor}
                loading={instance.loading}
                themeData={themeData}
                initialExpanded
              />
            </ConsolePageCustomizationContainer>
            <ConsolePageCustomizationContainer>
              <ButtonCustomizationPage
                buttonName="Secondary"
                externalMessages={messages}
                onChangeColor={this.onChangeColor}
                loading={instance.loading}
                themeData={themeData}
              />
            </ConsolePageCustomizationContainer>
            <ConsolePageCustomizationContainer>
              <ButtonCustomizationPage
                buttonName="Register"
                externalMessages={messages}
                onChangeColor={this.onChangeColor}
                loading={instance.loading}
                themeData={themeData}
                deploymentToggle
              />
            </ConsolePageCustomizationContainer>
            <ConsolePageCustomizationContainer>
              <ButtonCustomizationPage
                buttonName="SignIn"
                externalMessages={messages}
                onChangeColor={this.onChangeColor}
                loading={instance.loading}
                themeData={themeData}
                deploymentToggle
              />
            </ConsolePageCustomizationContainer>
            <ConsolePageCustomizationContainer>
              <ButtonCustomizationPage
                buttonName="Logistration"
                externalMessages={messages}
                onChangeColor={this.onChangeColor}
                loading={instance.loading}
                themeData={themeData}
                deploymentToggle
              />
            </ConsolePageCustomizationContainer>
          </div>
        )}
      </ConsolePage>
    );
  }
}

export const ThemeButtons = connect<
  StateProps,
  ActionProps,
  {},
  Props,
  RootState
>((state: RootState) => state.console, {
  updateThemeFieldValue
})(ThemeButtonsComponent);
