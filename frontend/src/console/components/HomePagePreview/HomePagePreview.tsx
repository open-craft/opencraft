import React from 'react';
import { Col, Row, Container } from 'react-bootstrap';
import {
  NavigationMenu,
  FooterPreview,
  CoursesListingItem
} from 'console/components';
import { InstanceSettingsModel } from 'console/models';
import { HeroPreview } from 'ui/components/HeroPreview';

interface HomePagePreviewProps {
  children?: React.ReactNode;
  instanceData: InstanceSettingsModel;
}

export const HomePagePreview: React.FC<HomePagePreviewProps> = (
  props: HomePagePreviewProps
) => {
  const { instanceData } = props;
  const themeData = instanceData.draftThemeConfig!;
  return (
    <>

        <Container className="theme-preview-navigation">
          <NavigationMenu instanceData={instanceData} themeData={themeData} />
        </Container>
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
    </>
  );
};
