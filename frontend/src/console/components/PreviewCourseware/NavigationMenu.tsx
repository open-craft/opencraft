import * as React from 'react';
// import messages from './displayMessages';
import './styles.scss';
import { Col, Row } from 'react-bootstrap';
import { ThemeSchema } from 'ocim-client';
import { CustomizableLink } from '../CustomizableLink';
import { InstanceSettingsModel } from '../../models';

interface NavigationMenuProps {
  children?: React.ReactNode;
  instanceData: InstanceSettingsModel | null;
  themeData: ThemeSchema;
  loggedIn?: boolean;
}

export const NavigationMenu: React.FC<NavigationMenuProps> = (
  props: NavigationMenuProps
) => {
  const { themeData } = props;

  return (
      <div>

    <Row
    className="main-menu navigation-menu"
    style={{ background: themeData.headerBg }}
    >
        <Col md={1} className="logo">
        {props.instanceData && props.instanceData.logo && (
            <img src={props.instanceData.logo} alt="Logo" />
            )}
        </Col>
        <Col md={2.5} className="courseware-header">
          <Row className="org-name">
              edX: DemoX
          </Row>
          <Row>
              Demostration Course
          </Row>
        </Col>
        <Col md={2} className="courseware-header">
          <CustomizableLink
              linkColor={themeData.mainNavLinkColor}
              borderBottomColor={themeData.mainNavItemBorderBottomColor}
              borderBottomHoverColor={themeData.mainNavItemHoverBorderBottomColor}
              >
              Discover New
          </CustomizableLink>
        </Col>
    </Row>
    <Row
      className="course-menu navigation-menu"
      style={{ background: themeData.headerBg }}
      >
      <Col md={1}>
        <CustomizableLink
          linkColor={themeData.mainNavLinkColor}
          borderBottomColor={themeData.mainNavItemBorderBottomColor}
          borderBottomHoverColor={themeData.mainNavItemHoverBorderBottomColor}
          active={props.loggedIn}
          >
          Course
        </CustomizableLink>
      </Col>
      <Col md={1}>
        <CustomizableLink
          linkColor={themeData.mainNavLinkColor}
          borderBottomColor={themeData.mainNavItemBorderBottomColor}
          borderBottomHoverColor={themeData.mainNavItemHoverBorderBottomColor}
          >
          Discussion
        </CustomizableLink>
      </Col>
      <Col md={1}>
        <CustomizableLink
          linkColor={themeData.mainNavLinkColor}
          borderBottomColor={themeData.mainNavItemBorderBottomColor}
          borderBottomHoverColor={themeData.mainNavItemHoverBorderBottomColor}
          >
          Wiki
        </CustomizableLink>
      </Col>
      <Col md={1}>
        <CustomizableLink
          linkColor={themeData.mainNavLinkColor}
          borderBottomColor={themeData.mainNavItemBorderBottomColor}
          borderBottomHoverColor={themeData.mainNavItemHoverBorderBottomColor}
          >
          Progress
        </CustomizableLink>
      </Col>
    </Row>
            </div>
  );
};
