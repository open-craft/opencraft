import * as React from 'react';
// import messages from './displayMessages';
import { Accordion, Card, Nav } from 'react-bootstrap';
import { ROUTES } from 'global/constants';
import './styles.scss';
import { useLocation, useHistory } from "react-router-dom";


export const CustomizationSideMenu: React.FC = () => {
  // Using a react hook to fetch full path and highlight currently active
  // page and extend correct accordion
  const currentLocation = useLocation().pathname;
  const history = useHistory();

  let activeKey = 0;
  if (currentLocation.includes("custom_pages")) {
    activeKey = 1;
  }
  else if (currentLocation.includes("settings")) {
    activeKey = 2;
  }

  const customNavLink = (name: string, link: string) => (<Nav.Link
      active={currentLocation === link}
      disabled={link === ""}
      onClick={() => history.push(link)}
    >
      {name}
    </Nav.Link>
  );

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
              {customNavLink("Preview & colors", "")}
              {customNavLink("Logos", "")}
              {customNavLink("Domain", "")}
              {customNavLink("Buttons", "")}
              {customNavLink("Navigation", "")}
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
              {customNavLink("About", "")}
              {customNavLink("Terms of Service", "")}
              {customNavLink("Contact", "")}
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
              {customNavLink("General", ROUTES.Console.INSTANCE_SETTINGS_GENERAL)}
              {customNavLink("Domain", "")}
            </Nav>
          </Card.Body>
        </Accordion.Collapse>
      </Card>
    </Accordion>
  );
};
