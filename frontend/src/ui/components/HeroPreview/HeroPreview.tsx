import * as React from 'react';
import './styles.scss';

interface HeroPreviewProps {
  homePageHeroTitleColor: undefined | string;
  homePageHeroSubtitleColor: undefined | string;
  homepageOverlayHtml: undefined | string;
}

export const HeroPreview: React.FC<HeroPreviewProps> = (
  props: HeroPreviewProps
) => {
  let titleStyles = {};
  let subtitleStyles = {};

  if (props.homePageHeroTitleColor) {
    titleStyles = {
      color: props.homePageHeroTitleColor
    };
  }

  if (props.homePageHeroSubtitleColor) {
    subtitleStyles = {
      color: props.homePageHeroSubtitleColor
    };
  }
  const heroTextRegex = /<h1>(.*)<\/h1><p>(.*)<\/p>/;
  let matched;
  if (props.homepageOverlayHtml) {
    matched = heroTextRegex.exec(props.homepageOverlayHtml as string);
  }
  return (
    <div className="hero-preview">
      <div className="outer-wrapper">
        <div className="title">
          <div className="heading-group">
            <h1 style={titleStyles}>{matched ? matched[1] : ''}</h1>
            <p style={subtitleStyles}>{matched ? matched[2] : ''}</p>
          </div>
        </div>
      </div>
    </div>
  );
};
