import * as React from 'react';
// import messages from './displayMessages';
import './styles.scss';
import { Col, Row } from 'react-bootstrap';
import { ThemeSchema } from 'ocim-client';
import avatar from 'assets/avatar-default.png';
// import { CustomizableButton } from '../CustomizableButton';  # TODO: uncomment in BB-2219.
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
        <CustomizableLink noHover>Register</CustomizableLink>
        <CustomizableLink noHover>Sign in</CustomizableLink>
        {/* TODO: Dummy buttons. While merging BB-2219 remove these from above and uncomment the ones below. */}
        {/* <CustomizableButton */}
        {/*  initialTextColor={themeData.btnRegisterColor} */}
        {/*  initialBackgroundColor={themeData.btnRegisterBg} */}
        {/*  initialBorderColor={themeData.btnRegisterBorderColor} */}
        {/*  initialHoverTextColor={themeData.btnRegisterHoverColor} */}
        {/*  initialHoverBackgroundColor={themeData.btnRegisterHoverBg} */}
        {/*  initialHoverBorderColor={themeData.btnRegisterHoverBorderColor} */}
        {/* > */}
        {/*  Register */}
        {/* </CustomizableButton> */}
        {/* <CustomizableButton */}
        {/*  initialTextColor={themeData.btnSignInColor} */}
        {/*  initialBackgroundColor={themeData.btnSignInBg} */}
        {/*  initialBorderColor={themeData.btnSignInBorderColor} */}
        {/*  initialHoverTextColor={themeData.btnSignInHoverColor} */}
        {/*  initialHoverBackgroundColor={themeData.btnSignInHoverBg} */}
        {/*  initialHoverBorderColor={themeData.btnSignInHoverBorderColor} */}
        {/* > */}
        {/*  Sign in */}
        {/* </CustomizableButton> */}
      </Col>
    </Row>
  );

  return (
    <Row
      className="main-navigation-menu navigation-menu"
      style={{ background: themeData.mainNavColor }}
    >
      <Col md={1}>
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
