import * as React from 'react';
import messages from './displayMessages';
import { WrappedMessage } from 'utils/intl';
import { Accordion, Card, Nav } from 'react-bootstrap';
import { ROUTES } from 'global/constants';
import './styles.scss';
import { useLocation, NavLink } from 'react-router-dom';

export const CustomizationSideMenu: React.FC = () => {
  // Using react hooks to fetch full path and highlight currently active
  // page and extend correct accordion.
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
            <WrappedMessage messages={messages} id="accordionTheme" />
          </Accordion.Toggle>
        </Card.Header>
        <Accordion.Collapse eventKey="0">
          <Card.Body>
            <Nav className="flex-column">
              <NavLink
                exact
                to=""
                className="disabled"
                onClick={e => {
                  e.preventDefault();
                }}
              >
                <WrappedMessage messages={messages} id="linkPreviewColors" />
              </NavLink>
              <NavLink
                exact
                to=""
                className="disabled"
                onClick={e => {
                  e.preventDefault();
                }}
              >
                <WrappedMessage messages={messages} id="linkLogos" />
              </NavLink>
              <NavLink
                exact
                to=""
                className="disabled"
                onClick={e => {
                  e.preventDefault();
                }}
              >
                <WrappedMessage messages={messages} id="linkButtons" />
              </NavLink>
              <NavLink
                exact
                to=""
                className="disabled"
                onClick={e => {
                  e.preventDefault();
                }}
              >
                <WrappedMessage messages={messages} id="linkNavigation" />
              </NavLink>
            </Nav>
          </Card.Body>
        </Accordion.Collapse>
      </Card>
      <Card>
        <Card.Header>
          <Accordion.Toggle as={Card.Header} variant="link" eventKey="1">
            <WrappedMessage messages={messages} id="accordionCustomPages" />
          </Accordion.Toggle>
        </Card.Header>
        <Accordion.Collapse eventKey="1">
          <Card.Body>
            <Nav className="flex-column">
              <NavLink
                exact
                to=""
                className="disabled"
                onClick={e => {
                  e.preventDefault();
                }}
              >
                <WrappedMessage messages={messages} id="linkAbout" />
              </NavLink>
              <NavLink
                exact
                to=""
                className="disabled"
                onClick={e => {
                  e.preventDefault();
                }}
              >
                <WrappedMessage messages={messages} id="linkTOS" />
              </NavLink>
              <NavLink
                exact
                to=""
                className="disabled"
                onClick={e => {
                  e.preventDefault();
                }}
              >
                <WrappedMessage messages={messages} id="linkContact" />
              </NavLink>
            </Nav>
          </Card.Body>
        </Accordion.Collapse>
      </Card>
      <Card>
        <Card.Header>
          <Accordion.Toggle as={Card.Header} variant="link" eventKey="2">
            <WrappedMessage messages={messages} id="accordionInstanceSettings" />
          </Accordion.Toggle>
        </Card.Header>
        <Accordion.Collapse eventKey="2">
          <Card.Body>
            <Nav defaultActiveKey="/home" className="flex-column">
              <NavLink exact to={ROUTES.Console.INSTANCE_SETTINGS_GENERAL}>
                <WrappedMessage messages={messages} id="linkGeneral" />
              </NavLink>
              <NavLink
                exact
                to=""
                className="disabled"
                onClick={e => {
                  e.preventDefault();
                }}
              >
                <WrappedMessage messages={messages} id="linkDomain" />
              </NavLink>
            </Nav>
          </Card.Body>
        </Accordion.Collapse>
      </Card>
    </Accordion>
  );
};