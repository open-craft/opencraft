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
  title: string;
  subtitle: string;
  // extra state to manage the empty title and subtitle and rendering
  renderBool: boolean;
}

interface ActionProps {
  clearErrorMessage: Function;
  updateThemeFieldValue: Function;
  updateImages: Function;
  updateStaticContentOverridesFieldValue: Function;
}

interface StateProps extends InstancesModel {}

interface Props extends StateProps, ActionProps {}

/**
 * Extracts title and subtitle from values coming from the backend
 * using regex and returns object.
 *
 * It requires passing props to allow use in componentDidUpdate with prevProps.
 * Return empty values if props don't exist yet.
 */
const getHeroContents = (props: Props) => {
  const instanceData = props.activeInstance.data;
  let title = '';
  let subtitle = '';

  if (
    instanceData &&
    instanceData.draftStaticContentOverrides &&
    instanceData.draftStaticContentOverrides.homepageOverlayHtml
  ) {
    const { draftStaticContentOverrides } = props.activeInstance.data!;
    const heroHtmlRegex = /^<h1>(.*)<\/h1><p>(.*)<\/p>$/;
    const matched = heroHtmlRegex.exec(
      draftStaticContentOverrides!.homepageOverlayHtml as string
    );
    // Update variables if matched
    title = matched ? matched[1] : '';
    subtitle = matched ? matched[2] : '';
  }

  return {
    title,
    subtitle
  };
};

export class HeroComponent extends React.PureComponent<Props, State> {
  constructor(props: Props) {
    super(props);

    this.state = {
      title: '',
      subtitle: '',
      renderBool: true
    };
  }

  public componentDidMount() {
    this.checkAndUpdateState();
  }

  public componentDidUpdate(prevProps: Props) {
    this.checkAndUpdateState();
    if (
      this.staticContentOverridesExists() &&
      this.staticContentOverridesExists(prevProps) &&
      prevProps.activeInstance.data!.draftStaticContentOverrides !==
        this.props.activeInstance.data!.draftStaticContentOverrides
    ) {
      this.checkNewAndUpdateState();
    }
  }

  private checkNewAndUpdateState = () => {
    if (this.homePageOverlayHtmlExists()) {
      const dataFromProps = getHeroContents(this.props);
      this.setState({
        title: dataFromProps.title,
        subtitle: dataFromProps.subtitle
      });
    }
  };

  private checkAndUpdateState = () => {
    if (
      this.homePageOverlayHtmlExists() &&
      (this.state.title.trim() === '' || this.state.subtitle.trim() === '') &&
      this.state.renderBool
    ) {
      const dataFromProps = getHeroContents(this.props);

      this.setState({
        title: dataFromProps.title,
        subtitle: dataFromProps.subtitle,
        renderBool: false
      });
    }
  };

  private activeInstanceDataExists = (props: Props = this.props) => {
    return props.activeInstance && props.activeInstance.data;
  };

  private themeConfigExists = (props: Props = this.props) => {
    return (
      this.activeInstanceDataExists(props) &&
      props.activeInstance.data!.draftThemeConfig
    );
  };

  private staticContentOverridesExists = (props: Props = this.props) => {
    return (
      this.activeInstanceDataExists(props) &&
      props.activeInstance.data!.draftStaticContentOverrides
    );
  };

  private homePageOverlayHtmlExists = (props: Props = this.props) => {
    return (
      this.activeInstanceDataExists(props) &&
      this.staticContentOverridesExists(props) &&
      props.activeInstance.data!.draftStaticContentOverrides!
        .homepageOverlayHtml
    );
  };

  private onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const field = e.target.name;
    const { value } = e.target;

    this.setState({
      [field]: value
    } as Pick<State, 'title' | 'subtitle'>);
  };

  private updateHeroText = () => {
    if (this.activeInstanceDataExists() && this.state.title.trim().length > 0) {
      const homepageOverlayHtml = `<h1>${this.state.title}</h1><p>${this.state.subtitle}</p>`;
      this.props.updateStaticContentOverridesFieldValue(
        this.props.activeInstance.data!.id,
        'homepageOverlayHtml',
        homepageOverlayHtml
      );
    }
    if (this.state.title.trim() === '' || this.state.subtitle.trim() === '') {
      this.setState({
        renderBool: true
      });
    }
  };

  resetHeroValue = (valueName: string) => {
    const data = {
      ...getHeroContents(this.props),
      [valueName]: ''
    };

    if (this.activeInstanceDataExists()) {
      const homepageOverlayHtml = `<h1>${data.title}</h1><p>${data.subtitle}</p>`;
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

    // Fixing state lifecycle management issues
    const dataFromProps = getHeroContents(this.props);
    const heroTitleKey = `title_${dataFromProps.title}`;
    const heroSubtitleKey = `subtitle_${dataFromProps.subtitle}`;

    if (this.themeConfigExists()) {
      themeData = instance.data!.draftThemeConfig;
    }

    if (this.staticContentOverridesExists()) {
      staticContentOverrides = instance.data!.draftStaticContentOverrides;
    }
    return (
      <ConsolePage contentLoading={this.props.loading}>
        <div className="hero-page">
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
              <div>
                <Row>
                  <Col>
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
                <CollapseEditArea initialExpanded>
                  <Row>
                    <Col>
                      <span className="section-title">
                        <WrappedMessage id="heroText" messages={messages} />
                      </span>
                    </Col>
                  </Row>
                  <Row className="title-customization-fields">
                    <Col md={6}>
                      <TextInputField
                        fieldName="title"
                        messages={messages}
                        value={this.state.title}
                        onBlur={this.updateHeroText}
                        onChange={this.onChange}
                        reset={() => {
                          this.resetHeroValue('title');
                        }}
                        key={heroTitleKey}
                      />
                    </Col>
                    <Col md={6}>
                      <TextInputField
                        fieldName="subtitle"
                        messages={messages}
                        value={this.state.subtitle}
                        onBlur={this.updateHeroText}
                        onChange={this.onChange}
                        reset={() => {
                          this.resetHeroValue('subtitle');
                        }}
                        key={heroSubtitleKey}
                      />
                    </Col>
                  </Row>

                  <Row>
                    <Col>
                      <span className="section-title">
                        <WrappedMessage id="heroStyling" messages={messages} />
                      </span>
                    </Col>
                  </Row>

                  <Row className="hero-customizations">
                    <Col key="heroTitleColor">
                      <ColorInputField
                        fieldName="homePageHeroTitleColor"
                        initialValue={themeData.homePageHeroTitleColor || ''}
                        onChange={this.onChangeColor}
                        messages={messages}
                        loading={instance.loading.includes('draftThemeConfig')}
                        hideTooltip
                      />
                    </Col>
                    <Col key="heroSubtitleColor">
                      <ColorInputField
                        fieldName="homePageHeroSubtitleColor"
                        initialValue={themeData.homePageHeroSubtitleColor || ''}
                        onChange={this.onChangeColor}
                        messages={messages}
                        loading={instance.loading.includes('draftThemeConfig')}
                        hideTooltip
                      />
                    </Col>
                  </Row>
                  <Row>
                    <Col>
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
                        recommendedSize="1200x250px"
                        reset={() => {
                          if (
                            this.activeInstanceDataExists() &&
                            instance.data!.heroCoverImage
                          ) {
                            this.removeImage('heroCoverImage');
                          }
                        }}
                      />
                    </Col>
                  </Row>
                </CollapseEditArea>
              </div>
            )}
          </ConsolePageCustomizationContainer>
        </div>
      </ConsolePage>
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
