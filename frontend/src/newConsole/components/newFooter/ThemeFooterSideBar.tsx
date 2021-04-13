import * as React from 'react';
import './styles.scss';
import { ConsolePageCustomizationContainer } from 'console/components';
import { ConsolePage } from 'newConsole/components';
import { Col, Row } from 'react-bootstrap';
import { InstancesModel } from 'console/models';
import { connect } from 'react-redux';
import { RootState } from 'global/state';

import { ColorInputField } from 'ui/components/ColorInputField';
import { updateThemeFieldValue } from 'console/actions';
import { WrappedMessage } from 'utils/intl';
import messages from './displayMessages';

interface State {}

interface ActionProps {
  updateThemeFieldValue: Function;
}

interface StateProps extends InstancesModel {}

interface Props extends StateProps, ActionProps {}

export class ThemeFooterSideBarComponent extends React.PureComponent<
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
      <ConsolePage contentLoading={this.props.loading} showSideBarEditComponent>
        {themeData && themeData.version === 1 && (
          <div className="footer-settings">
            <ConsolePageCustomizationContainer>
              <Row>
                <Col>
                  <h2>
                    <WrappedMessage
                      messages={messages}
                      id="newFooterSettings"
                    />
                  </h2>
                </Col>
              </Row>
              <Row>
                <Col>
                  <ColorInputField
                    fieldName="footerBg"
                    initialValue={themeData.footerBg}
                    onChange={this.onChangeColor}
                    messages={messages}
                    loading={instance.loading.includes('draftThemeConfig')}
                  />
                </Col>
              </Row>
              <Row>
                <Col>
                  <ColorInputField
                    fieldName="footerColor"
                    initialValue={themeData.footerColor}
                    onChange={this.onChangeColor}
                    messages={messages}
                    loading={instance.loading.includes('draftThemeConfig')}
                  />
                </Col>
              </Row>
              <Row>
                <Col>
                  <ColorInputField
                    fieldName="footerLinkColor"
                    initialValue={themeData.footerLinkColor}
                    onChange={this.onChangeColor}
                    messages={messages}
                    loading={instance.loading.includes('draftThemeConfig')}
                  />
                </Col>
              </Row>
            </ConsolePageCustomizationContainer>
          </div>
        )}
      </ConsolePage>
    );
  }
}

export const ThemeFooterSideBar = connect<
  StateProps,
  ActionProps,
  {},
  Props,
  RootState
>((state: RootState) => state.console, {
  updateThemeFieldValue
})(ThemeFooterSideBarComponent);
