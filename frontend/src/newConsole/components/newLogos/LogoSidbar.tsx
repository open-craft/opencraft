import * as React from 'react';
import './styles.scss';
import { ConsolePageCustomizationContainer } from 'console/components';
import { CustomizedConsolePage } from 'newConsole/components';
import { Row, Col } from 'react-bootstrap';
import { InstancesModel } from 'console/models';
import { CollapseEditArea, ImageUploadField } from 'ui/components';
import { connect } from 'react-redux';
import { RootState } from 'global/state';
import { WrappedMessage } from 'utils/intl';
import { clearErrorMessage, updateImages } from 'console/actions';
import messages from './displayMessages';

interface State {}
interface ActionProps {
  clearErrorMessage: Function;
  updateImages: Function;
}
interface StateProps extends InstancesModel {}
interface Props extends StateProps, ActionProps {
  history: {
    goBack: Function;
  };
}

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
    return (
      <CustomizedConsolePage
        contentLoading={this.props.loading}
        goBack={this.props.history.goBack}
      >
        <div className="custom-logo-pages">
          <ConsolePageCustomizationContainer>
            <Row>
              <Col md={9}>
                <h2>
                  <WrappedMessage messages={messages} id="logo" />
                </h2>
                <p>
                  <WrappedMessage messages={messages} id="logoDescription" />
                </p>
              </Col>
              <Col md={3} className="image-container">
                <div>
                  {instance.data && instance.data.logo && (
                    <img src={instance.data.logo} alt="Logo" />
                  )}
                </div>
              </Col>
            </Row>
            <CollapseEditArea initialExpanded>
              <ImageUploadField
                customUploadMessage={
                  <WrappedMessage messages={messages} id="uploadLogo" />
                }
                updateImage={(image: File) => {
                  this.updateImage('logo', image);
                }}
                recommendedSize="48x48 px"
                error={instance.feedback.logo}
                clearError={() => {
                  this.props.clearErrorMessage('logo');
                }}
              />
            </CollapseEditArea>
          </ConsolePageCustomizationContainer>

          <ConsolePageCustomizationContainer>
            <Row>
              <Col md={9}>
                <h2>
                  <WrappedMessage messages={messages} id="favicon" />
                </h2>
                <p>
                  <WrappedMessage messages={messages} id="faviconDescription" />
                </p>
              </Col>
              <Col md={3} className="image-container">
                <div>
                  {instance.data && instance.data.favicon && (
                    <img src={instance.data.favicon} alt="favicon" />
                  )}
                </div>
              </Col>
            </Row>
            <CollapseEditArea>
              <ImageUploadField
                customUploadMessage={
                  <WrappedMessage messages={messages} id="uploadFavicon" />
                }
                updateImage={(image: File) => {
                  this.updateImage('favicon', image);
                }}
                error={instance.feedback.favicon}
                clearError={() => {
                  this.props.clearErrorMessage('favicon');
                }}
              />
            </CollapseEditArea>
          </ConsolePageCustomizationContainer>
        </div>
      </CustomizedConsolePage>
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
  updateImages
})(LogosSideBarComponent);
