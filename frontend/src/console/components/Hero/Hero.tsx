import * as React from 'react';
import './styles.scss';
import {
  ConsolePage,
  ConsolePageCustomizationContainer
} from 'console/components';
import { Col, Row } from 'react-bootstrap';
import { InstancesModel } from 'console/models';
import {
  CollapseEditArea,
  ColorInputField,
  HeroPreview,
  ImageUploadField,
  TextInputField
} from 'ui/components';
import { connect } from 'react-redux';
import { RootState } from 'global/state';
import { WrappedMessage } from 'utils/intl';
import {
  clearErrorMessage,
  updateHeroText,
  updateImages,
  updateThemeFieldValue
} from 'console/actions';
import messages from './displayMessages';

interface State {}

interface ActionProps {
  clearErrorMessage: Function;
  updateHeroText: Function;
  updateThemeFieldValue: Function;
  updateImages: Function;
}
interface StateProps extends InstancesModel {}
interface Props extends StateProps, ActionProps {}

export class HeroComponent extends React.PureComponent<Props, State> {
  updateHeroTitle = (event: any) => {
    if (this.props.activeInstance && this.props.activeInstance.data) {
      this.props.updateHeroText(
        this.props.activeInstance.data.id,
        event.target.value,
        null
      );
    }
  };

  updateHeroSubtitle = (event: any) => {
    if (this.props.activeInstance && this.props.activeInstance.data) {
      this.props.updateHeroText(
        this.props.activeInstance.data.id,
        null,
        event.target.value
      );
    }
  };

  updateImage = (imageName: string, image: File) => {
    if (this.props.activeInstance && this.props.activeInstance.data) {
      this.props.updateImages(
        this.props.activeInstance.data.id,
        imageName,
        image
      );
    }
  };

  onChangeColor = (fieldName: string, newColor: string) => {
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
    const heroTextRegex = /<h1>(.*)<\/h1><p>(.*)<\/p>/;
    let matched = null;
    if (instance.data) {
      matched = heroTextRegex.exec(
        instance.data.draftStaticContentOverrides.homepageOverlayHtml
      );
    }
    return (
      <div className="hero-pages">
        <ConsolePage contentLoading={this.props.loading}>
          <ConsolePageCustomizationContainer>
            <Row>
              <Col md={9}>
                <h2>
                  <WrappedMessage messages={messages} id="hero" />
                </h2>
                <p>
                  <WrappedMessage messages={messages} id="heroDescription" />
                </p>
              </Col>
            </Row>
            <Row>
              <Col md={12}>
                {instance.data && <HeroPreview instanceData={instance.data} />}
              </Col>
            </Row>
            <CollapseEditArea initialExpanded>
              <Row>
                <Col md={12}>
                  <h2>
                    <WrappedMessage messages={messages} id="heroText" />
                  </h2>
                </Col>
              </Row>
              <Row>
                <Col md={6}>
                  <TextInputField
                    fieldName="title"
                    messages={messages}
                    value={matched ? matched[1] : ''}
                    onBlur={this.updateHeroTitle}
                    onChange={() => {}}
                  />
                </Col>
                <Col md={6}>
                  <TextInputField
                    fieldName="subTitle"
                    messages={messages}
                    value={matched ? matched[2] : ''}
                    onBlur={this.updateHeroSubtitle}
                    onChange={(event: any) => {
                      console.log('Title update', event.target.value);
                    }}
                  />
                </Col>
              </Row>
              <Row>
                <Col md={12}>
                  <h2>
                    <WrappedMessage
                      messages={messages}
                      id="heroCustomization"
                    />
                  </h2>
                </Col>
              </Row>
              <Row className="hero-customizations">
                <Col md={4}>
                  <ImageUploadField
                    customUploadMessage={(
                      <WrappedMessage
                        messages={messages}
                        id="uploadHeroCoverImage"
                      />
                    )}
                    recommendedSize="1200x250px"
                    updateImage={(image: File) => {
                      this.updateImage('heroCoverImage', image);
                    }}
                    error={instance.feedback.heroCoverImage}
                    clearError={() => {
                      this.props.clearErrorMessage('heroCover');
                    }}
                  />
                </Col>
                {themeData &&
                  themeData.version === 1 && [
                    <Col md={4} key="heroTitleColor">
                      <ColorInputField
                        fieldName="homePageHeroTitleColor"
                        initialValue={themeData.homePageHeroTitleColor}
                        onChange={this.onChangeColor}
                        messages={messages}
                        loading={instance.loading.includes('draftThemeConfig')}
                      />
                    </Col>,
                    <Col md={4} key="heroSubtitleColor">
                      <ColorInputField
                        fieldName="homePageHeroSubtitleColor"
                        initialValue={themeData.homePageHeroSubtitleColor}
                        onChange={this.onChangeColor}
                        messages={messages}
                        loading={instance.loading.includes('draftThemeConfig')}
                      />
                    </Col>
                  ]}
              </Row>
            </CollapseEditArea>
          </ConsolePageCustomizationContainer>
        </ConsolePage>
      </div>
    );
  }
}

export const Hero = connect<StateProps, ActionProps, {}, Props, RootState>(
  (state: RootState) => state.console,
  {
    clearErrorMessage,
    updateHeroText,
    updateThemeFieldValue,
    updateImages
  }
)(HeroComponent);
