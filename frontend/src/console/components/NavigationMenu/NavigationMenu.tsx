import * as React from 'react';
// import messages from './displayMessages';
import './styles.scss';
import { Col, Row } from 'react-bootstrap';
import { ThemeSchema } from 'ocim-client';
import avatar from 'assets/avatar-default.png';
import { CustomizableButton } from '../CustomizableButton';
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

  const userMenu = props.loggedIn ? (
    <Row className="navigation-menu navigation-submenu">
      <Col>
        <CustomizableLink linkColor={themeData.mainNavLinkColor} noHover>
          Help
        </CustomizableLink>
        <img src={avatar} alt="Avatar" />
        <CustomizableLink linkColor={themeData.mainNavLinkColor} noHover>
          JoeSoap
        </CustomizableLink>
        <CustomizableLink linkColor={themeData.userDropdownColor} noHover>
          <i className="fas fa-caret-down" />
        </CustomizableLink>
      </Col>
    </Row>
  ) : (
    <Row className="navigation-menu navigation-submenu">
      <Col>
        <CustomizableButton
          initialTextColor={
            themeData.customizeRegisterBtn
              ? themeData.btnRegisterColor
              : themeData.btnSecondaryColor
          }
          initialBackgroundColor={
            themeData.customizeRegisterBtn
              ? themeData.btnRegisterBg
              : themeData.btnSecondaryBg
          }
          initialBorderColor={
            themeData.customizeRegisterBtn
              ? themeData.btnRegisterBorderColor
              : themeData.btnSecondaryBorderColor
          }
          initialHoverTextColor={
            themeData.customizeRegisterBtn
              ? themeData.btnRegisterHoverColor
              : themeData.btnSecondaryHoverColor
          }
          initialHoverBackgroundColor={
            themeData.customizeRegisterBtn
              ? themeData.btnRegisterHoverBg
              : themeData.btnSecondaryHoverBg
          }
          initialHoverBorderColor={
            themeData.customizeRegisterBtn
              ? themeData.btnRegisterHoverBorderColor
              : themeData.btnSecondaryHoverBorderColor
          }
        >
          Register
        </CustomizableButton>
        <CustomizableButton
          initialTextColor={
            themeData.customizeSignInBtn
              ? themeData.btnSignInColor
              : themeData.btnPrimaryColor
          }
          initialBackgroundColor={
            themeData.customizeSignInBtn
              ? themeData.btnSignInBg
              : themeData.btnPrimaryBg
          }
          initialBorderColor={
            themeData.customizeSignInBtn
              ? themeData.btnSignInBorderColor
              : themeData.btnPrimaryBorderColor
          }
          initialHoverTextColor={
            themeData.customizeSignInBtn
              ? themeData.btnSignInHoverColor
              : themeData.btnPrimaryHoverColor
          }
          initialHoverBackgroundColor={
            themeData.customizeSignInBtn
              ? themeData.btnSignInHoverBg
              : themeData.btnPrimaryHoverBg
          }
          initialHoverBorderColor={
            themeData.customizeSignInBtn
              ? themeData.btnSignInHoverBorderColor
              : themeData.btnPrimaryHoverBorderColor
          }
        >
          Sign in
        </CustomizableButton>
      </Col>
    </Row>
  );

  return (
    <Row
      className="main-navigation-menu navigation-menu"
      style={{ background: themeData.headerBg }}
    >
      <Col md={1} className="logo">
        {props.instanceData && props.instanceData.logo && (
          <img src={props.instanceData.logo} alt="Logo" />
        )}
      </Col>
      <Col md={1}>
        <CustomizableLink
          linkColor={themeData.mainNavLinkColor}
          borderBottomColor={themeData.mainNavItemBorderBottomColor}
          borderBottomHoverColor={themeData.mainNavItemHoverBorderBottomColor}
          active={props.loggedIn}
        >
          Courses
        </CustomizableLink>
      </Col>
      <Col md={3}>
        <CustomizableLink
          linkColor={themeData.mainNavLinkColor}
          borderBottomColor={themeData.mainNavItemBorderBottomColor}
          borderBottomHoverColor={themeData.mainNavItemHoverBorderBottomColor}
        >
          Discover New
        </CustomizableLink>
      </Col>
      <Col md={7}>{userMenu}</Col>
    </Row>
  );
};
