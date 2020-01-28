import * as React from 'react';
import { Navbar, Nav, Container } from 'react-bootstrap';
import { ROUTES, CONTACT_US_LINK } from 'global/constants';
import { useLocation, useHistory } from 'react-router-dom';
import logo from 'assets/icons.svg';
import './styles.scss';

export const Header: React.FC = () => {
  const currentLocation = useLocation().pathname;
  const history = useHistory();

  // Workaround to check authentication on header instead of connecting
  // component to redux
  const authenticated = currentLocation.includes(ROUTES.Console.HOME);

  if (authenticated) {
    return (
      <Container>
        <Navbar bg="transparent" expand="lg" variant="dark">
          <Navbar.Brand className="logo-container mx-auto">
            <svg className="site-logo">
              <use xlinkHref={`${logo}#opencraft_logo`} />
            </svg>
          </Navbar.Brand>
          <Navbar.Toggle aria-controls="basic-navbar-nav" />
          <Navbar.Collapse id="basic-navbar-nav">
            <Nav className="ml-auto">
              <Nav.Link>Customize</Nav.Link>
              <Nav.Link onClick={() => window.open(CONTACT_US_LINK, '_blank')}>
                Support Request
              </Nav.Link>
              <Nav.Link disabled>Status & Notifications</Nav.Link>
              <Nav.Link
                onClick={() => {
                  history.push(ROUTES.Auth.LOGOUT);
                }}
              >
                Log out
              </Nav.Link>
            </Nav>
          </Navbar.Collapse>
        </Navbar>
      </Container>
    );
  }

  // Only show login link when on registration page and only show registration
  // link when on login page
  return (
    <Container>
      <Navbar bg="transparent" expand="md" variant="dark">
        <Navbar.Brand className="logo-container mx-auto">
          <svg className="site-logo">
            <use xlinkHref={`${logo}#opencraft_logo`} />
          </svg>
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="ml-auto">
            {currentLocation.includes(ROUTES.Registration.HOME) && (
              <Nav.Link onClick={() => history.push(ROUTES.Auth.LOGIN)}>
                Login
              </Nav.Link>
            )}
            {currentLocation.includes(ROUTES.Auth.LOGIN) && (
              <Nav.Link onClick={() => history.push(ROUTES.Registration.HOME)}>
                Create your account
              </Nav.Link>
            )}
          </Nav>
        </Navbar.Collapse>
      </Navbar>
    </Container>
  );
};
