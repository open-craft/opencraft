import * as React from 'react';
// import messages from './displayMessages';
import './styles.scss';
import { Col, Row } from 'react-bootstrap';
import { ThemeSchema } from 'ocim-client';
import { CustomizableButton } from '../CustomizableButton';
import { CustomizableLink } from '../CustomizableLink';

interface NavigationMenuProps {
  children?: React.ReactNode;
  themeData: ThemeSchema;
  loggedIn?: boolean;
}

export const NavigationMenu: React.FC<NavigationMenuProps> = (
  props: NavigationMenuProps
) => {
  const { themeData } = props;

  const userMenu = props.loggedIn ? (
    <Row className="navigation-menu navigation-submenu">
      <Col md={2}>
        <CustomizableLink linkColor={themeData.mainNavLinkColor}>
          Help
        </CustomizableLink>
      </Col>
      <Col md={3}>
        <img src="" alt="Avatar" />
      </Col>
      <Col md={3}>
        <CustomizableLink linkColor={themeData.mainNavLinkColor}>
          JoeSoap
        </CustomizableLink>
      </Col>
      <Col md={1}>
        <CustomizableLink linkColor={themeData.userDropdownColor}>
          <i className="fas fa-caret-down" />
        </CustomizableLink>
      </Col>
    </Row>
  ) : (
    <Row className="navigation-menu navigation-submenu">
      <Col>
        <CustomizableButton
          initialTextColor={themeData.btnRegisterColor}
          initialBackgroundColor={themeData.btnRegisterBg}
          initialBorderColor={themeData.btnRegisterBorderColor}
          initialHoverTextColor={themeData.btnRegisterHoverColor}
          initialHoverBackgroundColor={themeData.btnRegisterHoverBg}
          initialHoverBorderColor={themeData.btnRegisterHoverBorderColor}
        >
          Register
        </CustomizableButton>
      </Col>
      <Col>
        <CustomizableButton
          initialTextColor={themeData.btnSignInColor}
          initialBackgroundColor={themeData.btnSignInBg}
          initialBorderColor={themeData.btnSignInBorderColor}
          initialHoverTextColor={themeData.btnSignInHoverColor}
          initialHoverBackgroundColor={themeData.btnSignInHoverBg}
          initialHoverBorderColor={themeData.btnSignInHoverBorderColor}
        >
          Sign in
        </CustomizableButton>
      </Col>
    </Row>
  );

  return (
    <Row
      className="main-navigation-menu navigation-menu"
      style={{ background: themeData.mainNavColor }}
    >
      <Col md={1}>
        <img src="" alt="Logo" />
      </Col>
      <Col md={2}>
        <CustomizableLink
          linkColor={themeData.mainNavLinkColor}
          borderBottomColor={
            props.loggedIn ? themeData.mainNavItemBorderBottomColor : ''
          }
          borderBottomHoverColor={themeData.mainNavItemHoverBorderBottomColor}
        >
          Courses
        </CustomizableLink>
      </Col>
      <Col md={3}>
        <CustomizableLink
          linkColor={themeData.mainNavLinkColor}
          borderBottomHoverColor={themeData.mainNavItemHoverBorderBottomColor}
        >
          Discover New
        </CustomizableLink>
      </Col>
      <Col md={5} style={{ marginLeft: '60px' }}>
        {userMenu}
      </Col>
    </Row>
  );
};
