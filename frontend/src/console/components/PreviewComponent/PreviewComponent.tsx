import * as React from 'react';
import dummyCourse from 'assets/dummy_course.png';
import './styles.scss';
import { ThemeSchema } from 'ocim-client';
import { Col, Row } from 'react-bootstrap';
import { NavigationMenu } from '../NavigationMenu';
import { InstanceSettingsModel } from '../../models';
import { HeroPreview } from '../../../ui/components/HeroPreview';
import { FooterPreview } from '../FooterPreview';

interface PreviewComponentProps {
  children?: React.ReactNode;
  instanceData: InstanceSettingsModel;
  themeData: ThemeSchema;
}

export const PreviewComponent: React.FC<PreviewComponentProps> = (
  props: PreviewComponentProps
) => {
  const { themeData } = props;

  return (
    <div className="theme-preview">
      <Row className="theme-preview-navigation">
        <Col className="theme-preview-navigation">
          <NavigationMenu
            instanceData={props.instanceData}
            themeData={themeData}
          />
        </Col>
      </Row>
      <div className="theme-home">
        <Row className="theme-hero-container">
          <Col>
            <HeroPreview
              heroCoverImage={props.instanceData.heroCoverImage || ''}
              homePageHeroTitleColor={themeData.homePageHeroTitleColor}
              homePageHeroSubtitleColor={themeData!.homePageHeroSubtitleColor}
              homepageOverlayHtml={
                props.instanceData.draftStaticContentOverrides!
                  .homepageOverlayHtml
              }
            />
          </Col>
        </Row>
        <Row className="theme-courses-container">
          <Col>
            {/* TOOD: Replace with actual component. */}
            <img src={dummyCourse} alt="dummy course" />
          </Col>
        </Row>
      </div>
      <Row className="theme-footer">
        <Col>
          <FooterPreview
            instanceData={props.instanceData}
            themeData={themeData}
          />
        </Col>
      </Row>
    </div>
  );
};
