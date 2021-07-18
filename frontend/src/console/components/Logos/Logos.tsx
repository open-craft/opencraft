import * as React from 'react';
import './styles.scss';
import {
  ConsolePage,
  ConsolePageCustomizationContainer
} from 'console/components';
import { Row, Col } from 'react-bootstrap';
import { InstancesModel } from 'console/models';
import { ImageUploadField } from 'ui/components';
import { IntlContext } from 'react-intl';
import { connect } from 'react-redux';
import { RootState } from 'global/state';
import { WrappedMessage } from 'utils/intl';
import { clearErrorMessage, updateImages } from 'console/actions';
import faviconTooltipImage from 'assets/faviconTooltipImage.png';
import messages from './displayMessages';

interface State {}
interface ActionProps {
  clearErrorMessage: Function;
  updateImages: Function;
}
interface StateProps extends InstancesModel {}
interface Props extends StateProps, ActionProps {}

export class LogosComponent extends React.PureComponent<Props, State> {
  updateImage = (imageName: string, image: File) => {
    if (this.props.activeInstance && this.props.activeInstance.data) {
      this.props.updateImages(
        this.props.activeInstance.data.id,
        imageName,
        image,
        this.context
      );
    }
  };

  public render() {
    const instance = this.props.activeInstance;

    return (
      <ConsolePage contentLoading={this.props.loading}>
        <div className="custom-logo-pages">
          <ConsolePageCustomizationContainer>
            <h2>
              <WrappedMessage messages={messages} id="logos" />
            </h2>
            <Row>
              <Col md={3} className="image-container">
                <div>
                  {instance.data && instance.data.logo && (
                    <img src={instance.data.logo} alt="Logo" />
                  )}
                </div>
              </Col>
            </Row>
            <ImageUploadField
              customUploadMessage={
                <WrappedMessage messages={messages} id="siteLogo" />
              }
              updateImage={(image: File) => {
                this.updateImage('logo', image);
              }}
              parentMessages={messages}
              recommendationTextId="logoRecommendation"
              error={instance.feedback.logo}
              clearError={() => {
                this.props.clearErrorMessage('logo');
              }}
              tooltipTextId="logoTooltip"
            />
            <Row>
              <Col md={3} className="image-container">
                <div>
                  {instance.data && instance.data.favicon && (
                    <img src={instance.data.favicon} alt="Favicon" />
                  )}
                </div>
              </Col>
            </Row>
            <ImageUploadField
              customUploadMessage={
                <WrappedMessage messages={messages} id="favicon" />
              }
              updateImage={(image: File) => {
                this.updateImage('favicon', image);
              }}
              parentMessages={messages}
              recommendationTextId="faviconRecommendation"
              error={instance.feedback.favicon}
              clearError={() => {
                this.props.clearErrorMessage('favicon');
              }}
              tooltipTextId="faviconTooltip"
              tooltipImage={faviconTooltipImage}
            />
          </ConsolePageCustomizationContainer>
        </div>
      </ConsolePage>
    );
  }
}

LogosComponent.contextType = IntlContext;

export const Logos = connect<StateProps, ActionProps, {}, Props, RootState>(
  (state: RootState) => state.console,
  {
    clearErrorMessage,
    updateImages
  }
)(LogosComponent);
