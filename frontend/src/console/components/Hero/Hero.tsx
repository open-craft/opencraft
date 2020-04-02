import * as React from 'react';
import { InstancesModel } from 'console/models';
import { StaticContentOverrides, ThemeSchema } from 'ocim-client';
import {
  ConsolePage,
  ConsolePageCustomizationContainer
} from 'console/components';
import { WrappedMessage } from 'utils/intl';
import { Col, Row } from 'react-bootstrap';
import {
  CollapseEditArea,
  ColorInputField,
  HeroPreview,
  ImageUploadField,
  TextInputField
} from 'ui/components';
import {
  clearErrorMessage,
  updateImages,
  updateStaticContentOverridesFieldValue,
  updateThemeFieldValue
} from 'console/actions';
import { RootState } from 'global/state';
import { connect } from 'react-redux';
import messages from './displayMessages';
import './styles.scss';

interface State {
  [key: string]: string;

  title: string;
  subtitle: string;
}

interface ActionProps {
  clearErrorMessage: Function;
  updateThemeFieldValue: Function;
  updateImages: Function;
  updateStaticContentOverridesFieldValue: Function;
}

interface StateProps extends InstancesModel {}

interface Props extends StateProps, ActionProps {}

export class HeroComponent extends React.PureComponent<Props, State> {
  constructor(props: Props) {
    super(props);

    this.state = {
      title: '',
      subtitle: ''
    };

    if (this.homePageOverlayHtmlExists()) {
      const {
        homepageOverlayHtml
      } = props.activeInstance.data!.draftStaticContentOverrides!;
      const heroHtmlRegex = /^<h1>(.*)<\/h1><p>(.*)<\/p>$/;
      const matched = heroHtmlRegex.exec(homepageOverlayHtml as string);
      if (matched) {
        this.state = {
          title: matched[1],
          subtitle: matched[2]
        };
      }
    }
  }

  private activeInstanceDataExists = () => {
    return this.props.activeInstance && this.props.activeInstance.data;
  };

  private themeConfigExists = () => {
    return (
      this.activeInstanceDataExists() &&
      this.props.activeInstance.data!.draftThemeConfig
    );
  };

  private staticContentOverridesExists = () => {
    return (
      this.activeInstanceDataExists() &&
      this.props.activeInstance.data!.draftStaticContentOverrides
    );
  };

  private homePageOverlayHtmlExists = () => {
    return (
      this.activeInstanceDataExists() &&
      this.staticContentOverridesExists() &&
      this.props.activeInstance.data!.draftStaticContentOverrides!
        .homepageOverlayHtml
    );
  };

  private onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const field = e.target.name;
    const { value } = e.target;

    this.setState({
      [field]: value
    });
  };

  private updateHeroText = () => {
    if (this.activeInstanceDataExists()) {
      const homepageOverlayHtml = `<h1>${this.state.title}</h1><p>${this.state.subtitle}</p>`;
      this.props.updateStaticContentOverridesFieldValue(
        this.props.activeInstance.data!.id,
        'homepageOverlayHtml',
        homepageOverlayHtml
      );
    }
  };

  private onChangeColor = (fieldName: string, newColor: string) => {
    if (this.activeInstanceDataExists()) {
      this.props.updateThemeFieldValue(
        this.props.activeInstance.data!.id,
        fieldName,
        newColor
      );
    }
  };

  private updateImage = (imageName: string, image: File) => {
    if (this.activeInstanceDataExists()) {
      this.props.updateImages(
        this.props.activeInstance.data!.id,
        imageName,
        image
      );
    }
  };

  private removeImage = (imageName: string) => {
    if (this.activeInstanceDataExists()) {
      this.props.updateImages(
        this.props.activeInstance.data!.id,
        imageName,
        ''
      );
    }
  };

  public render() {
    const instance = this.props.activeInstance;
    let themeData: undefined | ThemeSchema;
    let staticContentOverrides: undefined | StaticContentOverrides;

    if (this.themeConfigExists()) {
      themeData = instance.data!.draftThemeConfig;
    }

    if (this.staticContentOverridesExists()) {
      staticContentOverrides = instance.data!.draftStaticContentOverrides;
    }
    return (
      <div className="hero-page">
        <ConsolePage contentLoading={this.props.loading}>
          <ConsolePageCustomizationContainer>
            <Row>
              <Col md={9}>
                <h2>
                  <WrappedMessage id="hero" messages={messages} />
                </h2>
                <p>
                  <WrappedMessage id="heroDescription" messages={messages} />
                </p>
              </Col>
            </Row>
            {themeData && themeData.version === 1 && (
              <Row>
                <Col md={12}>
                  {this.themeConfigExists() &&
                    this.staticContentOverridesExists() && (
                      <HeroPreview
                        heroCoverImage={instance.data!.heroCoverImage || ''}
                        homePageHeroTitleColor={
                          themeData.homePageHeroTitleColor
                        }
                        homePageHeroSubtitleColor={
                          themeData!.homePageHeroSubtitleColor
                        }
                        homepageOverlayHtml={
                          staticContentOverrides!.homepageOverlayHtml
                        }
                      />
                    )}
                </Col>
              </Row>
            )}
            <CollapseEditArea initialExpanded>
              <Row>
                <Col md={12}>
                  <h2>
                    <WrappedMessage id="heroText" messages={messages} />
                  </h2>
                </Col>
              </Row>
              <Row>
                <Col md={6}>
                  <TextInputField
                    fieldName="title"
                    messages={messages}
                    value={this.state.title}
                    onBlur={this.updateHeroText}
                    onChange={this.onChange}
                  />
                </Col>
                <Col md={6}>
                  <TextInputField
                    fieldName="subtitle"
                    messages={messages}
                    value={this.state.subtitle}
                    onBlur={this.updateHeroText}
                    onChange={this.onChange}
                  />
                </Col>
              </Row>
              <Row className="hero-customizations">
                <Col md={4}>
                  <ImageUploadField
                    // prettier-ignore
                    customUploadMessage={(
                      <WrappedMessage id="uploadHeroCoverImage" messages={messages} />
                  )}
                    updateImage={(image: File) => {
                      this.updateImage('heroCoverImage', image);
                    }}
                    clearError={() => {
                      this.props.clearErrorMessage('heroCover');
                    }}
                  />
                  {this.activeInstanceDataExists() &&
                    instance.data!.heroCoverImage && (
                      <button
                        className="reset-value"
                        type="button"
                        onClick={() => {
                          this.removeImage('heroCoverImage');
                        }}
                      >
                        Remove
                      </button>
                    )}
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
    updateThemeFieldValue,
    updateImages,
    updateStaticContentOverridesFieldValue
  }
)(HeroComponent);
