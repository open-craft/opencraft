import * as React from 'react';
// import messages from './displayMessages';
import { Accordion, Card, Nav } from 'react-bootstrap';
import { ROUTES } from 'global/constants';
import './styles.scss';
import { useLocation, NavLink } from 'react-router-dom';

export const CustomizationSideMenu: React.FC = () => {
  // Using react hooks to fetch full path and highlight currently active
  // page and extend correct accordion and push pages to history.
  const currentLocation = useLocation().pathname;

  let activeKey = 0;
  if (currentLocation.includes('custom_pages')) {
    activeKey = 1;
  } else if (currentLocation.includes('settings')) {
    activeKey = 2;
  }

  return (
    <Accordion defaultActiveKey={`${activeKey}`} className="customization-menu">
      <Card>
        <Card.Header>
          <Accordion.Toggle as={Card.Header} variant="link" eventKey="0">
            Theme
          </Accordion.Toggle>
        </Card.Header>
        <Accordion.Collapse eventKey="0">
          <Card.Body>
            <Nav className="flex-column">
              <NavLink exact to={''} className="disabled" onClick={(e) => {e.preventDefault()}}>
                Preview & colors
              </NavLink>
              <NavLink exact to={''} className="disabled" onClick={(e) => {e.preventDefault()}}>
                Logos
              </NavLink>
              <NavLink exact to={''} className="disabled" onClick={(e) => {e.preventDefault()}}>
                Domain
              </NavLink>
              <NavLink exact to={''} className="disabled" onClick={(e) => {e.preventDefault()}}>
                Buttons
              </NavLink>
              <NavLink exact to={''} className="disabled" onClick={(e) => {e.preventDefault()}}>
                Navigation
              </NavLink>
            </Nav>
          </Card.Body>
        </Accordion.Collapse>
      </Card>
      <Card>
        <Card.Header>
          <Accordion.Toggle as={Card.Header} variant="link" eventKey="1">
            Custom Pages
          </Accordion.Toggle>
        </Card.Header>
        <Accordion.Collapse eventKey="1">
          <Card.Body>
            <Nav className="flex-column">
              <NavLink exact to={''} className="disabled" onClick={(e) => {e.preventDefault()}}>
                About
              </NavLink>
              <NavLink exact to={''} className="disabled" onClick={(e) => {e.preventDefault()}}>
                Terms of Service
              </NavLink>
              <NavLink exact to={''} className="disabled" onClick={(e) => {e.preventDefault()}}>
                Contact
              </NavLink>
            </Nav>
          </Card.Body>
        </Accordion.Collapse>
      </Card>
      <Card>
        <Card.Header>
          <Accordion.Toggle as={Card.Header} variant="link" eventKey="2">
            Instance Settings
          </Accordion.Toggle>
        </Card.Header>
        <Accordion.Collapse eventKey="2">
          <Card.Body>
            <Nav defaultActiveKey="/home" className="flex-column">
              <NavLink exact to={ROUTES.Console.INSTANCE_SETTINGS_GENERAL}>
                General
              </NavLink>
              <NavLink exact to={''} className="disabled" onClick={(e) => {e.preventDefault()}}>
                Domain
              </NavLink>
            </Nav>
          </Card.Body>
        </Accordion.Collapse>
      </Card>
    </Accordion>
  );
};
