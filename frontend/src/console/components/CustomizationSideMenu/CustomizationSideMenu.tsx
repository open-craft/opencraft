import * as React from 'react';
import { WrappedMessage } from 'utils/intl';
import { Accordion, Card, Nav } from 'react-bootstrap';
import { ROUTES, AVAILABLE_CUSTOM_PAGES } from 'global/constants';
import './styles.scss';
import { useLocation, NavLink } from 'react-router-dom';
import { capitalizeFirstLetter } from 'utils/string_utils';
import messages from './displayMessages';

export const CustomizationSideMenu: React.FC = () => {
  // Using react hooks to fetch full path and highlight currently active
  // page and extend correct accordion.
  const currentLocation = useLocation().pathname;

  let activeKey = 0;
  if (currentLocation.includes('custom-pages')) {
    activeKey = 1;
  } else if (currentLocation.includes('settings')) {
    activeKey = 2;
  } else if (currentLocation.includes('courses')) {
    activeKey = 3;
  }

  const customPageLink = (pageName: string) => {
    const pageRoute = ROUTES.Console.CUSTOM_PAGES.replace(
      ':pageName',
      pageName
    );
    const intlString = `customPage${capitalizeFirstLetter(pageName)}`;

    return (
      <NavLink exact to={pageRoute} key={`static_page_${pageName}`}>
        <WrappedMessage messages={messages} id={intlString} />
      </NavLink>
    );
  };

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
              <NavLink exact to={ROUTES.Console.THEME_PREVIEW_AND_COLORS}>
                <WrappedMessage messages={messages} id="linkPreviewColors" />
              </NavLink>
              <NavLink exact to={ROUTES.Console.LOGOS}>
                <WrappedMessage messages={messages} id="linkLogos" />
              </NavLink>
              <NavLink exact to={ROUTES.Console.THEME_BUTTONS}>
                <WrappedMessage messages={messages} id="linkButtons" />
              </NavLink>
              <NavLink exact to={ROUTES.Console.THEME_NAVIGATION}>
                <WrappedMessage messages={messages} id="linkNavigation" />
              </NavLink>
              <NavLink exact to={ROUTES.Console.THEME_FOOTER}>
                <WrappedMessage messages={messages} id="linkFooter" />
              </NavLink>
              <NavLink exact to={ROUTES.Console.HERO}>
                <WrappedMessage messages={messages} id="linkHero" />
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
              {AVAILABLE_CUSTOM_PAGES.map(pageName => {
                return customPageLink(pageName);
              })}
            </Nav>
          </Card.Body>
        </Accordion.Collapse>
      </Card>
      <Card>
        <Card.Header>
          <Accordion.Toggle as={Card.Header} variant="link" eventKey="2">
            <WrappedMessage
              messages={messages}
              id="accordionInstanceSettings"
            />
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
      <Card>
        <Card.Header>
          <Accordion.Toggle as={Card.Header} variant="link" eventKey="3">
            <WrappedMessage messages={messages} id="accordionCourses" />
          </Accordion.Toggle>
        </Card.Header>
        <Accordion.Collapse eventKey="3">
          <Card.Body>
            <Nav className="flex-column">
              <NavLink exact to={ROUTES.Console.COURSES}>
                <WrappedMessage messages={messages} id="linkManageCourses" />
              </NavLink>
            </Nav>
          </Card.Body>
        </Accordion.Collapse>
      </Card>
    </Accordion>
  );
};
