import * as React from 'react';
import './styles.scss';
import { ConsolePageCustomizationContainer } from 'console/components';
import { InstancesModel } from 'console/models';
import { ImageUploadField, TextInputField } from 'ui/components';
import { ConsolePage } from 'newConsole/components';
import faviconTooltipImage from 'assets/faviconTooltipImage.png';
import { connect } from 'react-redux';
import { RootState } from 'global/state';
import { WrappedMessage } from 'utils/intl';
import {
  clearErrorMessage,
  updateActiveInstanceField,
  updateImages,
  syncActiveInstanceField
} from 'console/actions';
import messages from 'console/components/Logos/displayMessages';

interface State {}
interface ActionProps {
  clearErrorMessage: typeof clearErrorMessage;
  updateImages: typeof updateImages;
  updateFieldValue: typeof updateActiveInstanceField;
  syncFieldValue: typeof syncActiveInstanceField;
}
interface StateProps extends InstancesModel {}
interface Props extends StateProps, ActionProps {}

export class LogosSideBarComponent extends React.PureComponent<Props, State> {
  updateImage = (imageName: string, image: File) => {
    if (this.props.activeInstance && this.props.activeInstance.data) {
      this.props.updateImages(
        this.props.activeInstance.data.id,
        imageName,
        image
      );
    }
  };

  public render() {
    const instance = this.props.activeInstance;
    let logo;
    let favicon;

    if (instance.data && instance.data.logo) {
      logo = instance.data.logo;
    }
    if (instance.data && instance.data.favicon) {
      favicon = instance.data.favicon;
    }
    const footerLogoImageSourceInput = (
      <ImageUploadField
        customUploadMessage={
          <WrappedMessage messages={messages} id="footerLogoImage" />
        }
        updateImage={(image: File) => {
          this.updateImage('footerLogoImage', image);
        }}
        parentMessages={messages}
        error={instance.feedback.footerLogoImage}
        clearError={() => {
          this.props.clearErrorMessage('footerLogoImage');
        }}
        tooltipTextId="footerLogoImageTooltip"
        innerPreview={instance.data?.footerLogoImage}
      >
        <p>
          <WrappedMessage messages={messages} id="footerLogoImageAdvice" />
        </p>
        <p>
          <a
            href="https://www.edx.org/trademarks"
            rel="noopener noreferrer"
            target="_blank"
          >
            <WrappedMessage
              messages={messages}
              id="footerOpenedxTrademarkLink"
            />
          </a>
        </p>
      </ImageUploadField>
    );
    const footerLogoUrlInput = (
      <TextInputField
        error={instance.feedback.footerLogoUrl}
        fieldName="footerLogoUrl"
        helpMessageId="footerLogoUrlHelp"
        loading={instance.loading.includes('footerLogoUrl')}
        messages={messages}
        onBlur={() => this.props.syncFieldValue('footerLogoUrl')}
        onChange={e => {
          this.props.updateFieldValue('footerLogoUrl', e.target.value);
        }}
        type="url"
        value={instance.data?.footerLogoUrl}
      />
    );

    return (
      <ConsolePage contentLoading={this.props.loading} showSideBarEditComponent>
        <div className="custom-logo-pages">
          <ConsolePageCustomizationContainer>
            <div className="sidebar-item">
              <h2 className="custom-logo-title">
                <WrappedMessage messages={messages} id="logos" />
              </h2>
            </div>
            <div className="logo-upload-field sidebar-item">
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
                innerPreview={logo}
              />
            </div>
            <div className="favicon-upload-field sidebar-item">
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
                innerPreview={favicon}
              />
            </div>
            <div className="favicon-upload-field sidebar-item">
              {footerLogoImageSourceInput}
              {footerLogoUrlInput}
            </div>
          </ConsolePageCustomizationContainer>
        </div>
      </ConsolePage>
    );
  }
}

export const LogosSideBar = connect<
  StateProps,
  ActionProps,
  {},
  Props,
  RootState
>((state: RootState) => state.console, {
  clearErrorMessage,
  updateFieldValue: updateActiveInstanceField,
  updateImages,
  syncFieldValue: syncActiveInstanceField
})(LogosSideBarComponent);
