import * as React from 'react';
import './styles.scss';
import {
  ConsolePage,
  ConsolePageCustomizationContainer,
  PreviewComponent
} from 'console/components';
import { ColorInputField } from 'ui/components';
import { InstancesModel } from 'console/models';
import { Container, Col, Row } from 'react-bootstrap';
import { connect } from 'react-redux';
import { RootState } from 'global/state';
import { WrappedMessage } from 'utils/intl';
import { updateThemeFieldValue } from 'console/actions';
import messages from './displayMessages';

interface State {}
interface ActionProps {
  updateThemeFieldValue: Function;
}
interface StateProps extends InstancesModel {}
interface Props extends StateProps, ActionProps {}

export class ThemePreviewAndColorsComponent extends React.PureComponent<
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
            <WrappedMessage messages={messages} id="themePreviewAndColors" />
          </h2>

          {themeData && themeData.version === 1 && (
            <Container className="theme-colors-and-prevew-container">
              <Row>
                <Col className="side-buttons">
                  <ColorInputField
                    fieldName="mainColor"
                    initialValue={themeData.mainColor}
                    onChange={this.onChangeColor}
                    messages={messages}
                    loading={instance.loading.includes('draftThemeConfig')}
                  />
                  <ColorInputField
                    fieldName="linkColor"
                    initialValue={themeData.linkColor}
                    onChange={this.onChangeColor}
                    messages={messages}
                    loading={instance.loading.includes('draftThemeConfig')}
                  />
                </Col>
                <Col xs={9}>
                  <PreviewComponent
                    instanceData={instance.data!}
                    themeData={themeData}
                  />
                </Col>
              </Row>
            </Container>
          )}
        </ConsolePageCustomizationContainer>
      </ConsolePage>
    );
  }
}

export const ThemePreviewAndColors = connect<
  StateProps,
  ActionProps,
  {},
  Props,
  RootState
>((state: RootState) => state.console, {
  updateThemeFieldValue
})(ThemePreviewAndColorsComponent);
