import logo from 'assets/icons.svg';
import * as React from 'react';
import {
  Navbar,
  Nav,
  Container
} from 'react-bootstrap';
import './styles.scss';

export const Header: React.FC = () => (
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
          <Nav.Link href="#home">Login</Nav.Link>
        </Nav>
      </Navbar.Collapse>
    </Navbar>
  </Container>
);
