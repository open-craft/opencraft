import * as React from 'react';
import './styles.scss';
import {
  ConsolePage,
  ConsolePageCustomizationContainer,
  CustomFooter
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

export class ThemeFooterComponent extends React.PureComponent<Props, State> {
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
            <WrappedMessage messages={messages} id="themeFooter" />
          </h2>

          {themeData && themeData.version === 1 && (
            <div className="theme-footer-container">
              <CustomFooter
                instanceData={instance.data}
                themeData={themeData}
              />
              <Row>
                <p className="style-name">
                  <WrappedMessage messages={messages} id="footerSettings" />
                </p>
              </Row>
              <Row>
                <Col md={4}>
                  <ColorInputField
                    fieldName="footerBg"
                    initialValue={themeData.footerBg}
                    onChange={this.onChangeColor}
                    messages={messages}
                    loading={instance.loading.includes('draftThemeConfig')}
                    hideTooltip
                  />
                </Col>
                <Col md={4}>
                  <ColorInputField
                    fieldName="footerColor"
                    initialValue={themeData.footerColor}
                    onChange={this.onChangeColor}
                    messages={messages}
                    loading={instance.loading.includes('draftThemeConfig')}
                    hideTooltip
                  />
                </Col>
                <Col md={4}>
                  <ColorInputField
                    fieldName="footerLinkColor"
                    initialValue={themeData.footerLinkColor}
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

export const ThemeFooter = connect<
  StateProps,
  ActionProps,
  {},
  Props,
  RootState
>((state: RootState) => state.console, {
  updateThemeFieldValue
})(ThemeFooterComponent);
