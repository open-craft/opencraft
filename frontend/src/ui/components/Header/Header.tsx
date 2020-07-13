import * as React from 'react';
import { Container, Nav, Navbar } from 'react-bootstrap';
import { CONTACT_US_LINK, ROUTES } from 'global/constants';
import { NavLink, Route } from 'react-router-dom';
import logo from 'assets/icons.svg';
import './styles.scss';

export const Header: React.FC = () => {
  // Only show login link when on registration page and only show registration
  // link when on login page
  return (
    <Container>
      <Navbar bg="transparent" expand="md" variant="dark">
        <Navbar.Brand className="logo-container mx-auto">
          <NavLink className="nav-link" to="/">
            <svg className="site-logo">
              <use xlinkHref={`${logo}#opencraft_logo`} />
            </svg>
          </NavLink>
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="ml-auto">
            <Route path={ROUTES.Registration.HOME}>
              <NavLink className="nav-link" to={ROUTES.Auth.LOGIN}>
                Login
              </NavLink>
            </Route>
            <Route path={ROUTES.Auth.LOGIN}>
              <NavLink className="nav-link" to={ROUTES.Registration.HOME}>
                Create your account
              </NavLink>
            </Route>
            <Route path={ROUTES.Console.HOME}>
              <NavLink className="nav-link" to={ROUTES.Console.HOME}>
                Customize
              </NavLink>
              <Nav.Link onClick={() => window.open(CONTACT_US_LINK, '_blank')}>
                Support Request
              </Nav.Link>
              <NavLink className="nav-link" to={ROUTES.Console.NOTICE_BOARD}>
                Status & Notifications
              </NavLink>
              <NavLink className="nav-link" to={ROUTES.Auth.LOGOUT}>
                Log out
              </NavLink>
            </Route>
          </Nav>
        </Navbar.Collapse>
      </Navbar>
    </Container>
  );
};
