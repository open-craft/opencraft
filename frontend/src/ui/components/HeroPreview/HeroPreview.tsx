import * as React from 'react';
import './styles.scss';
import { InstanceSettingsModel } from 'console/models';

interface HeroPreviewProps {
  instanceData: InstanceSettingsModel;
}

export const HeroPreview: React.FC<HeroPreviewProps> = (
  props: HeroPreviewProps
) => {
  const titleStyles = {
    color: props.instanceData.draftThemeConfig!.homePageHeroTitleColor
  };
  const subtitleStyles = {
    color: props.instanceData.draftThemeConfig!.homePageHeroSubtitleColor
  };
  const heroTextRegex = /<h1>(.*)<\/h1><p>(.*)<\/p>/;
  const matched = heroTextRegex.exec(
    props.instanceData!.draftStaticContentOverrides.homepageOverlayHtml as string
  );
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
