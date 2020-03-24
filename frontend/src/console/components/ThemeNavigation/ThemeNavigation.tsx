import * as React from 'react';
import './styles.scss';
import {
  ConsolePage,
  ConsolePageCustomizationContainer,
  NavigationMenu
} from 'console/components';
import { InstancesModel } from 'console/models';
import { connect } from 'react-redux';
import { RootState } from 'global/state';
import { updateThemeFieldValue } from 'console/actions';
import { Col, Row } from 'react-bootstrap';
import { ColorInputField } from '../../../ui/components/ColorInputField';
import messages from './displayMessages';
import { WrappedMessage } from '../../../utils/intl';

interface State {}

interface ActionProps {
  updateThemeFieldValue: Function;
}

interface StateProps extends InstancesModel {}

interface Props extends StateProps, ActionProps {}

export class ThemeNavigationComponent extends React.PureComponent<
  Props,
  State
> {
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
        <ConsolePageCustomizationContainer>
          <h2>
            <WrappedMessage messages={messages} id="themeNavigation" />
          </h2>

          {themeData && themeData.version === 1 && (
            <div className="theme-navigation-container">
              <NavigationMenu themeData={themeData} />
              <NavigationMenu themeData={themeData} loggedIn />
              <Row>
                <p className="style-name">
                  <WrappedMessage messages={messages} id="navigationLinks" />
                </p>
              </Row>
              <Row>
                <Col md={4}>
                  <ColorInputField
                    fieldName="mainNavColor"
                    initialValue={themeData.mainNavColor}
                    onChange={this.onChangeColor}
                    messages={messages}
                    loading={instance.loading.includes('draftThemeConfig')}
                    hideTooltip
                  />
                </Col>
                <Col md={4}>
                  <ColorInputField
                    fieldName="mainNavLinkColor"
                    initialValue={themeData.mainNavLinkColor}
                    onChange={this.onChangeColor}
                    messages={messages}
                    loading={instance.loading.includes('draftThemeConfig')}
                    hideTooltip
                  />
                </Col>
                <Col md={4}>
                  <ColorInputField
                    fieldName="mainNavItemBorderBottomColor"
                    initialValue={themeData.mainNavItemBorderBottomColor}
                    onChange={this.onChangeColor}
                    messages={messages}
                    loading={instance.loading.includes('draftThemeConfig')}
                    hideTooltip
                  />
                </Col>
              </Row>
              <Row>
                <Col md={4}>
                  <ColorInputField
                    fieldName="mainNavItemHoverBorderBottomColor"
                    initialValue={themeData.mainNavItemHoverBorderBottomColor}
                    onChange={this.onChangeColor}
                    messages={messages}
                    loading={instance.loading.includes('draftThemeConfig')}
                    hideTooltip
                  />
                </Col>
                <Col md={4}>
                  <ColorInputField
                    fieldName="userDropdownColor"
                    initialValue={themeData.userDropdownColor}
                    onChange={this.onChangeColor}
                    messages={messages}
                    loading={instance.loading.includes('draftThemeConfig')}
                    hideTooltip
                  />
                </Col>
              </Row>
            </div>
          )}
        </ConsolePageCustomizationContainer>
      </ConsolePage>
    );
  }
}

export const ThemeNavigation = connect<
  StateProps,
  ActionProps,
  {},
  Props,
  RootState
>((state: RootState) => state.console, {
  updateThemeFieldValue
})(ThemeNavigationComponent);
