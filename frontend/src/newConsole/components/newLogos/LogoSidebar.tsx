import * as React from 'react';
import './styles.scss';
import { ConsolePageCustomizationContainer } from 'console/components';
import { InstancesModel } from 'console/models';
import {
  ModalImageInput,
  OverlayTooltip,
  TextInputField2
} from 'ui/components';
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
import { IntlContext } from 'react-intl';

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
  updateImage = (imageName: string) => {
    return (image: File) => {
      if (this.props.activeInstance && this.props.activeInstance.data) {
        this.props.updateImages(
          this.props.activeInstance.data.id,
          imageName,
          image,
          this.context
        );
      }
    };
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
    const footerLogoImageSourceMessage = (
      <WrappedMessage messages={messages} id="footerLogoImage" />
    );
    const footerLogoImageSourceInput = (
      <>
        <h4 className="font-weight-bold">
          {footerLogoImageSourceMessage}
          <OverlayTooltip id="footerLogoImageTooltip">
            <WrappedMessage messages={messages} id="footerLogoImageTooltip" />
          </OverlayTooltip>
        </h4>
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
        <ModalImageInput
          customUploadMessage={footerLogoImageSourceMessage}
          updateImage={this.updateImage('footerLogoImage')}
          parentMessages={messages}
          error={instance.feedback.footerLogoImage}
          clearError={() => {
            this.props.clearErrorMessage('footerLogoImage');
          }}
          innerPreview={instance.data?.footerLogoImage}
        />
      </>
    );
    const footerLogoUrlInput = (
      <TextInputField2
        error={instance.feedback.footerLogoUrl}
        fieldName="footerLogoUrl"
        helpMessage={
          <WrappedMessage id="footerLogoUrlHelp" messages={messages} />
        }
        label={
          <h4 className="font-weight-bold">
            <WrappedMessage id="footerLogoUrl" messages={messages} />
          </h4>
        }
        loading={instance.loading.includes('footerLogoUrl')}
        onBlur={() => this.props.syncFieldValue('footerLogoUrl')}
        onChange={e => {
          this.props.updateFieldValue('footerLogoUrl', e.target.value);
        }}
        type="url"
        value={instance.data?.footerLogoUrl}
      />
    );

    const siteLogoMessage = (
      <WrappedMessage messages={messages} id="siteLogo" />
    );
    const faviconMessage = <WrappedMessage messages={messages} id="favicon" />;

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
              <h4 className="font-weight-bold">
                {siteLogoMessage}
                <OverlayTooltip id="logoTooltip">
                  <WrappedMessage messages={messages} id="logoTooltip" />
                </OverlayTooltip>
              </h4>
              <ModalImageInput
                customUploadMessage={siteLogoMessage}
                updateImage={this.updateImage('logo')}
                parentMessages={messages}
                recommendationTextId="logoRecommendation"
                error={instance.feedback.logo}
                clearError={() => {
                  this.props.clearErrorMessage('logo');
                }}
                innerPreview={logo}
              />
            </div>
            <div className="favicon-upload-field sidebar-item">
              <h4 className="font-weight-bold">
                {faviconMessage}
                <OverlayTooltip id="favicon" tooltipImage={faviconTooltipImage}>
                  <WrappedMessage messages={messages} id="faviconTooltip" />
                </OverlayTooltip>
              </h4>
              <ModalImageInput
                customUploadMessage={faviconMessage}
                updateImage={this.updateImage('favicon')}
                parentMessages={messages}
                recommendationTextId="faviconRecommendation"
                error={instance.feedback.favicon}
                clearError={() => {
                  this.props.clearErrorMessage('favicon');
                }}
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

LogosSideBarComponent.contextType = IntlContext;

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
