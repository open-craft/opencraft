import * as React from 'react';
import { RootState } from 'global/state';
import { connect } from 'react-redux';
import { Navbar, Nav, Container } from 'react-bootstrap';
import { performLogout } from 'auth/actions';
import logo from 'assets/icons.svg';
import './styles.scss';


interface ActionProps {
  performLogout: Function;
}

interface StateProps {
  refresh: string;
}

interface Props extends StateProps, ActionProps {}

export class HeaderComponent extends React.PureComponent<Props> {
  private renderAuthenticatedHeader = () => {
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
              <Nav.Link>Support Request</Nav.Link>
              <Nav.Link>Status & Notifications</Nav.Link>
              <Nav.Link onClick={() => {this.props.performLogout()}}>Log out</Nav.Link>
            </Nav>
          </Navbar.Collapse>
        </Navbar>
      </Container>
    );
  };

  private renderUnauthenticatedHeader = () => {
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
              <Nav.Link href="/login">Login</Nav.Link>
            </Nav>
          </Navbar.Collapse>
        </Navbar>
      </Container>
    );
  };

  public render() {
    let authenticated = !!(this.props.refresh);
    if (authenticated) {
      return this.renderAuthenticatedHeader()
    } else {
      return this.renderUnauthenticatedHeader()
    }
  }
};

export const Header = connect<StateProps, ActionProps, {}, Props, RootState>(
  (state: RootState) => ({
    refresh: state.loginState.refresh
  }),
  {
    performLogout
  }
)(HeaderComponent);
