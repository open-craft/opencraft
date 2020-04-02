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
  updateStaticContentOverridesFieldValue,
  updateThemeFieldValue
} from 'console/actions';
import messages from './displayMessages';

interface State {
  [key: string]: string;
  title: string;
  subtitle: string;
}

interface ActionProps {
  clearErrorMessage: Function;
  updateHeroText: Function;
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

    if (this.props.activeInstance.data) {
      const {
        homepageOverlayHtml
      } = this.props.activeInstance.data.draftStaticContentOverrides;
      const heroTextRegex = /<h1>(.*)<\/h1><p>(.*)<\/p>/;
      const matched = heroTextRegex.exec(homepageOverlayHtml);
      if (matched) {
        this.state = {
          title: matched[1],
          subtitle: matched[2]
        };
      }
    }
  }

  public componentDidUpdate(prevProps: Props) {
    // Fill fields after finishing loading data
    this.needToUpdateStaticContentOverridesFields(prevProps);
  }

  private needToUpdateStaticContentOverridesFields = (prevProps: Props) => {
    if (
      prevProps.activeInstance.loading.includes(
        'draftStaticContentOverrides'
      ) &&
      !this.props.activeInstance.loading.includes('draftStaticContentOverrides')
    ) {
      const {
        homepageOverlayHtml
      } = this.props.activeInstance!.data!.draftStaticContentOverrides;
      const heroTextRegex = /<h1>(.*)<\/h1><p>(.*)<\/p>/;
      const matched = heroTextRegex.exec(homepageOverlayHtml);
      if (matched) {
        this.setState({
          title: matched[1],
          subtitle: matched[2]
        });
      }
    }
  };

  private onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const field = e.target.name;
    const { value } = e.target;

    this.setState({
      [field]: value
    });
  };

  private updateHeroText = () => {
    if (this.props.activeInstance && this.props.activeInstance.data) {
      const homepageOverlayHtml = `<h1>${this.state.title}</h1><p>${this.state.subtitle}</p>`;
      this.props.updateStaticContentOverridesFieldValue(
        this.props.activeInstance.data.id,
        'homepageOverlayHtml',
        homepageOverlayHtml
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
                    // prettier-ignore
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
    updateImages,
    updateStaticContentOverridesFieldValue
  }
)(HeroComponent);
