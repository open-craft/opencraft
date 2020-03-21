import * as React from 'react';
import './styles.scss';
import {ConsolePage, ConsolePageCustomizationContainer, NavigationMenu} from 'console/components';
import {InstancesModel} from 'console/models';
import {connect} from 'react-redux';
import {RootState} from 'global/state';
import {updateThemeFieldValue} from 'console/actions';
import {Col, Row} from 'react-bootstrap';
import {ColorInputField} from '../../../ui/components/ColorInputField';
import messages from './displayMessages';

interface State {
}

interface ActionProps {
  updateThemeFieldValue: Function;
}

interface StateProps extends InstancesModel {
}

interface Props extends StateProps, ActionProps {
}

export class ThemeNavigationComponent extends React.PureComponent<Props,
  State> {
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
          {themeData && themeData.version === 1 && (
            <div className="theme-navigation-container">
              <NavigationMenu themeData={themeData}/>
              <br/>
              <NavigationMenu themeData={themeData} loggedIn/>
              <Row>
                <Col>
                  <ColorInputField
                    fieldName="mainNavColor"
                    initialValue={themeData.mainNavColor}
                    onChange={this.onChangeColor}
                    messages={messages}
                    loading={instance.loading.includes('draftThemeConfig')}
                    hideTooltip
                  />
                </Col>
                <Col>
                  <ColorInputField
                    fieldName="mainNavLinkColor"
                    initialValue={themeData.mainNavLinkColor}
                    onChange={this.onChangeColor}
                    messages={messages}
                    loading={instance.loading.includes('draftThemeConfig')}
                    hideTooltip
                  />
                </Col>
                <Col>
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
                <Col>
                  <ColorInputField
                    fieldName="mainNavItemHoverBorderBottomColor"
                    initialValue={themeData.mainNavItemHoverBorderBottomColor}
                    onChange={this.onChangeColor}
                    messages={messages}
                    loading={instance.loading.includes('draftThemeConfig')}
                    hideTooltip
                  />
                </Col>
                <Col>
                  <ColorInputField
                    fieldName="userDropdownColor"
                    initialValue={themeData.userDropdownColor}
                    onChange={this.onChangeColor}
                    messages={messages}
                    loading={instance.loading.includes('draftThemeConfig')}
                    hideTooltip
                  />
                </Col>
                <Col md={3}/>
              </Row>
            </div>

          )}
        </ConsolePageCustomizationContainer>
      </ConsolePage>
    );
  }
}

export const ThemeNavigation = connect<StateProps,
  ActionProps,
  {},
  Props,
  RootState>((state: RootState) => state.console, {
  updateThemeFieldValue
})(ThemeNavigationComponent);
