import * as React from 'react';
import { Container, Nav, Navbar } from 'react-bootstrap';
import { CONTACT_US_LINK, ROUTES } from 'global/constants';
import { Route, useHistory } from 'react-router-dom';
import logo from 'assets/icons.svg';
import './styles.scss';

export const Header: React.FC = () => {
  const history = useHistory();

  const navigateTo = (route:string) => () => history.push(route);

  // Only show login link when on registration page and only show registration
  // link when on login page
  return (
    <Container>
      <Navbar bg="transparent" expand="md" variant="dark">
        <Navbar.Brand className="logo-container mx-auto">
          <Nav.Link onClick={navigateTo(ROUTES.Console.HOME)}>
            <svg className="site-logo">
              <use xlinkHref={`${logo}#opencraft_logo`}/>
            </svg>
          </Nav.Link>
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav"/>
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="ml-auto">
            <Route path={ROUTES.Registration.HOME}>
              <Nav.Link onClick={navigateTo(ROUTES.Auth.LOGIN)}>
                Login
              </Nav.Link>
            </Route>
            <Route path={ROUTES.Auth.LOGIN}>
              <Nav.Link onClick={navigateTo(ROUTES.Registration.HOME)}>
                Create your account
              </Nav.Link>
            </Route>
            <Route path={ROUTES.Console.HOME}>
              <Nav.Link>Customize</Nav.Link>
              <Nav.Link onClick={() => window.open(CONTACT_US_LINK, '_blank')}>
                Support Request
              </Nav.Link>
              <Nav.Link disabled>Status & Notifications</Nav.Link>
              <Nav.Link onClick={navigateTo(ROUTES.Auth.LOGOUT)}>
                Log out
              </Nav.Link>
            </Route>
          </Nav> </Navbar.Collapse>
      </Navbar>
    </Container>
  );
};
