import * as React from 'react';
import './styles.scss';
import {ConsolePage, CustomizableButton} from 'console/components';
import {CollapseEditArea, ColorInputField} from 'ui/components';
import { InstancesModel } from 'console/models';
import {Container, Col, Row, OverlayTrigger, Tooltip} from 'react-bootstrap';
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

export class ThemeButtonsComponent extends React.PureComponent<
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
    console.log(themeData);

    const tooltip = (
      <Tooltip id="redeployment-status">
        <WrappedMessage messages={messages} id={`themePrimaryButtonHelp`} />
      </Tooltip>
    );

    return (
      <ConsolePage contentLoading={this.props.loading}>
        {themeData && themeData.version === 1 && (
          <div>
            <Row>
              <Col md={9}>
                <WrappedMessage messages={messages} id="themePrimaryButton" />
                <OverlayTrigger placement="right" overlay={tooltip}>
                  <div className="info-icon">
                    <i className="fas fa-info-circle"/>
                  </div>
                </OverlayTrigger>
              </Col>
              <Col md={3}>
                <CustomizableButton
                  initialBackgroundColor={themeData.btnPrimaryColor}
                  initialTextColor={themeData.btnPrimaryBg}
                  initialBorderBlockColor={themeData.btnPrimaryBorderColor}
                  initialHoverBackgroundColor={themeData.btnPrimaryHoverColor}
                  initialHoverTextColor={themeData.btnPrimaryHoverBg}
                  initialHoverBorderBlockColor={themeData.btnPrimaryHoverBorderColor}
                />
              </Col>
            </Row>

            <CollapseEditArea initialExpanded={true}>
              <Container className="theme-colors-and-prevew-container">
                <Row><h2>Active styles</h2></Row>
                <Row>
                  <Col>
                    <ColorInputField
                      fieldName="btnPrimaryBg"
                      initialValue={themeData.btnPrimaryBg}
                      onChange={this.onChangeColor}
                      messages={messages}
                      loading={instance.loading.includes('draftThemeConfig')}
                      hideTooltip={true}
                    />
                  </Col>
                  <Col>
                    <ColorInputField
                      fieldName="btnPrimaryColor"
                      initialValue={themeData.btnPrimaryColor}
                      onChange={this.onChangeColor}
                      messages={messages}
                      loading={instance.loading.includes('draftThemeConfig')}
                      hideTooltip={true}
                    />
                  </Col>
                  <Col>
                    <ColorInputField
                      fieldName="btnPrimaryBorderColor"
                      initialValue={themeData.btnPrimaryBorderColor}
                      onChange={this.onChangeColor}
                      messages={messages}
                      loading={instance.loading.includes('draftThemeConfig')}
                      hideTooltip={true}
                    />
                  </Col>
                </Row>
              </Container>
            </CollapseEditArea>

            <CollapseEditArea initialExpanded={false}>
              <Container className="theme-colors-and-prevew-container">
                <Row><h2>Hover state styles</h2></Row>
                <Row>
                  <Col>
                    <ColorInputField
                      fieldName="btnPrimaryHoverBg"
                      initialValue={themeData.btnPrimaryHoverBg}
                      onChange={this.onChangeColor}
                      messages={messages}
                      loading={instance.loading.includes('draftThemeConfig')}
                      hideTooltip={true}
                    />
                  </Col>
                  <Col>
                    <ColorInputField
                      fieldName="btnPrimaryHoverColor"
                      initialValue={themeData.btnPrimaryHoverColor}
                      onChange={this.onChangeColor}
                      messages={messages}
                      loading={instance.loading.includes('draftThemeConfig')}
                      hideTooltip={true}
                    />
                  </Col>
                  <Col>
                    <ColorInputField
                      fieldName="btnPrimaryHoverBorderColor"
                      initialValue={themeData.btnPrimaryHoverBorderColor}
                      onChange={this.onChangeColor}
                      messages={messages}
                      loading={instance.loading.includes('draftThemeConfig')}
                      hideTooltip={true}
                    />
                  </Col>
                </Row>
              </Container>
            </CollapseEditArea>
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
