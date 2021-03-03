import * as React from 'react';
import './styles.scss';
import { Col, Row } from 'react-bootstrap';
import { NavigationMenu } from '../NavigationMenu';
import { InstanceSettingsModel } from '../../models';
import { HeroPreview } from '../../../ui/components/HeroPreview';
import { FooterPreview } from '../FooterPreview';
import { CoursesListingItem } from '../CoursesListingItem';

interface PreviewComponentProps {
  children?: React.ReactNode;
  instanceData: InstanceSettingsModel;
  currentPreview: string;
}

export const PreviewComponent: React.FC<PreviewComponentProps> = (
  props: PreviewComponentProps
) => {
  const { instanceData } = props;
  const themeData = instanceData.draftThemeConfig!;

  // To Do: Edit this to taste when implementing the other previews
  if (props.currentPreview === 'dashboard') {
    return (
      <div className="theme-preview">
        <Row className="theme-preview-navigation">
          <Col className="theme-preview-navigation">
            <NavigationMenu instanceData={instanceData} themeData={themeData} />
          </Col>
        </Row>
        <div className="theme-home">
          <Row className="theme-hero-container">
            <Col>
              <HeroPreview
                heroCoverImage={instanceData.heroCoverImage || ''}
                homePageHeroTitleColor={themeData.homePageHeroTitleColor}
                homePageHeroSubtitleColor={themeData.homePageHeroSubtitleColor}
                homepageOverlayHtml={
                  instanceData!.draftStaticContentOverrides &&
                  instanceData.draftStaticContentOverrides.homepageOverlayHtml
                }
              />
            </Col>
          </Row>
          <Row className="theme-courses-container">
            <Col md={3} className="theme-courses-item">
              <CoursesListingItem themeData={themeData} />
            </Col>
          </Row>
        </div>
        <Row className="theme-footer">
          <Col>
            <FooterPreview instanceData={instanceData} themeData={themeData} />
          </Col>
        </Row>
      </div>
    );
  }
  return <div className="theme-preview" />;
};
