import { InstancesModel } from 'console/models';
import { RootState } from 'global/state';
import * as React from 'react';
import { connect } from 'react-redux';
import { WrappedMessage } from 'utils/intl';
import { updateThemeFieldValue } from 'console/actions';
import {
  ConsolePage,
  ButtonCustomizationComponent
} from 'newConsole/components';

import messages from './displayMessages';
import './styles.scss';

interface State {}
interface ActionProps {
  updateThemeFieldValue: Function;
}
interface StateProps extends InstancesModel {}
interface Props extends StateProps, ActionProps {}

class ButtonsCustomizationPage extends React.PureComponent<Props, State> {
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
      <ConsolePage contentLoading={this.props.loading} showSideBarEditComponent>
        <h1 className="edit-heading">
          <WrappedMessage messages={messages} id="buttons" />
        </h1>
        {themeData && themeData.version === 1 && (
          <div className="theme-buttons-container">
            <ButtonCustomizationComponent
              buttonName="Primary"
              externalMessages={messages}
              onChangeColor={this.onChangeColor}
              loading={instance.loading}
              themeData={themeData}
              initialExpanded
            />
            <ButtonCustomizationComponent
              buttonName="Secondary"
              externalMessages={messages}
              onChangeColor={this.onChangeColor}
              loading={instance.loading}
              themeData={themeData}
            />
            <ButtonCustomizationComponent
              buttonName="Register"
              externalMessages={messages}
              onChangeColor={this.onChangeColor}
              loading={instance.loading}
              themeData={themeData}
              deploymentToggle
            />
            <ButtonCustomizationComponent
              buttonName="SignIn"
              externalMessages={messages}
              onChangeColor={this.onChangeColor}
              loading={instance.loading}
              themeData={themeData}
              deploymentToggle
            />
            <ButtonCustomizationComponent
              buttonName="Logistration"
              externalMessages={messages}
              onChangeColor={this.onChangeColor}
              loading={instance.loading}
              themeData={themeData}
              deploymentToggle
            />
          </div>
        )}
      </ConsolePage>
    );
  }
}

export const ButtonsCustomization = connect<
  StateProps,
  ActionProps,
  {},
  Props,
  RootState
>((state: RootState) => state.console, {
  updateThemeFieldValue
})(ButtonsCustomizationPage);
