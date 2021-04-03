import * as React from 'react';
import { Container, Nav, Navbar, NavDropdown } from 'react-bootstrap';
import { FAQ_PAGE_LINK, ROUTES } from 'global/constants';
import { NavLink, Route } from 'react-router-dom';
import { InstancesModel } from 'console/models';
import { RootState } from 'global/state';
import { connect } from 'react-redux';
import logo from 'assets/icons.svg';
import { WrappedMessage } from 'utils/intl';
import { DeploymentIndicator } from '../CustomStatusPill';
import messages from './displayMessages';
import './styles.scss';

interface StateProps extends InstancesModel {}

interface Props extends StateProps {
  children: React.ReactNode;
  access: string;
}

export const HeaderComponent: React.FC<Props> = (props: Props) => {
  // Only show login link when on registration page and only show registration
  // link when on login page

  let lmsUrl = null;
  let deploymentPill = null;

  if (!props.loading && props.activeInstance.data !== null) {
    // if active instance data is available, get lms link
    lmsUrl = props.activeInstance.data.lmsUrl;

    // build the deployment status indicator
    const { deployment } = props.activeInstance;
    deploymentPill = (
      <DeploymentIndicator
        deploymentType={deployment?.deploymentType}
        redeploymentStatus={deployment?.status}
      />
    );
  }

  return (
    <Navbar expand="md" variant="dark">
      <Container
        fluid
        className="d-flex flex-wrap align-items-center justify-content-between px-4 py-3"
      >
        <Navbar.Brand className="logo-container mr-auto order-0">
          <NavLink className="navbar-brand-link" to={ROUTES.Console.HOME}>
            <svg className="site-logo">
              <use xlinkHref={`${logo}#opencraft_logo`} />
            </svg>
          </NavLink>
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" className="order-1" />
        <Navbar.Collapse id="basic-navbar-nav" className="order-3 order-md-2">
          <Nav className="ml-auto">
            <Route path={ROUTES.Registration.HOME}>
              <Nav.Link
                className="nav-link"
                target="_blank"
                href={FAQ_PAGE_LINK}
              >
                <WrappedMessage messages={messages} id="faq" />
              </Nav.Link>
              {props.access !== '' ? (
                <NavLink className="nav-link" to={ROUTES.Console.HOME}>
                  <WrappedMessage messages={messages} id="goToConsole" />
                </NavLink>
              ) : (
                <NavLink className="nav-link" to={ROUTES.Auth.LOGIN}>
                  <WrappedMessage messages={messages} id="login" />
                </NavLink>
              )}
            </Route>
            <Route path={ROUTES.Auth.LOGIN}>
              <NavLink className="nav-link" to={ROUTES.Registration.HOME}>
                <WrappedMessage messages={messages} id="registration" />
              </NavLink>
            </Route>
            <Route path={ROUTES.Console.HOME}>
              <NavLink
                className="nav-link"
                to={ROUTES.Console.HOME}
                isActive={(match, location) => {
                  // Mark this link as `active` for all customization pages.
                  return location.pathname.startsWith(ROUTES.Console.HOME);
                }}
              >
                <WrappedMessage messages={messages} id="customize" />
              </NavLink>

              {lmsUrl && (
                <a
                  href={lmsUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="nav-link nav-lms-link"
                >
                  {deploymentPill}
                  <span>
                    <WrappedMessage messages={messages} id="visitLMS" />
                  </span>
                  <i className="fa fa-external-link-alt externalLinkIcon" />
                </a>
              )}
            </Route>
          </Nav>
        </Navbar.Collapse>
        <Nav className="accounts-dropdown-nav order-2 order-md-3">
          <Route path={ROUTES.Console.HOME}>
            <NavDropdown
              title={<i className="fa fa-user-circle account-dropdown-icon" />}
              alignRight
              id="accounts-dropdown"
            >
              <NavLink
                exact
                to=""
                className="dropdown-item disabled"
                onClick={e => {
                  e.preventDefault();
                }}
              >
                <WrappedMessage messages={messages} id="account" />
              </NavLink>
              <NavLink
                className="dropdown-item"
                to={ROUTES.Console.INSTANCE_SETTINGS_GENERAL}
              >
                <WrappedMessage messages={messages} id="siteSettings" />
              </NavLink>
              <NavLink
                exact
                to=""
                className="dropdown-item disabled"
                onClick={e => {
                  e.preventDefault();
                }}
              >
                <WrappedMessage messages={messages} id="domain" />
              </NavLink>
              <NavLink
                className="dropdown-item"
                to={ROUTES.Console.NOTICE_BOARD}
              >
                <WrappedMessage messages={messages} id="noticeBoard" />
              </NavLink>
              <NavLink className="dropdown-item" to={ROUTES.Auth.LOGOUT}>
                <WrappedMessage messages={messages} id="logout" />
              </NavLink>
            </NavDropdown>
          </Route>
        </Nav>
      </Container>
    </Navbar>
  );
};

export const Header = connect<StateProps, {}, {}, Props, RootState>(
  (state: RootState) => ({
    ...state.loginState,
    ...state.console
  })
)(HeaderComponent);
