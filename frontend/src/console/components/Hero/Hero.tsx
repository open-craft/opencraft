import * as React from 'react';
import { InstancesModel } from 'console/models';
import { ThemeSchema } from 'ocim-client';
import { ConsolePage } from 'newConsole/components';
import { WrappedMessage } from 'utils/intl';
import {
  ColorInputField,
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
import { Col, Row } from 'react-bootstrap';
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
  const instanceData = props.activeInstance!.data;
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

    // Fixing state lifecycle management issues
    const dataFromProps = getHeroContents(this.props);
    const heroTitleKey = `title_${dataFromProps.title}`;
    const heroSubtitleKey = `subtitle_${dataFromProps.subtitle}`;

    if (this.themeConfigExists()) {
      themeData = instance.data!.draftThemeConfig;
    }
    return (
      <ConsolePage contentLoading={this.props.loading} showSideBarEditComponent>
        <div className="hero-page">
          {themeData && themeData.version === 1 && (
            <div>
              <h1 className="edit-heading">
                <WrappedMessage messages={messages} id="Hero" />
              </h1>
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
              <Row>
                <Col>
                  <ColorInputField
                    fieldName="homePageHeroTitleColor"
                    initialValue={themeData.homePageHeroTitleColor || ''}
                    onChange={this.onChangeColor}
                    messages={messages}
                    loading={instance.loading.includes('draftThemeConfig')}
                  />
                  <ColorInputField
                    fieldName="homePageHeroSubtitleColor"
                    initialValue={themeData.homePageHeroSubtitleColor || ''}
                    onChange={this.onChangeColor}
                    messages={messages}
                    loading={instance.loading.includes('draftThemeConfig')}
                  />
                </Col>
              </Row>
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
                parentMessages={messages}
                recommendationTextId="heroRecommendation"
                reset={() => {
                  if (
                    this.activeInstanceDataExists() &&
                    instance.data!.heroCoverImage
                  ) {
                    this.removeImage('heroCoverImage');
                  }
                }}
              />
            </div>
          )}
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
