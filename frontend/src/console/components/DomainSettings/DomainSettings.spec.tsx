import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { DomainSettings } from './DomainSettings';

it('renders correctly for no externalDomain', () => {
  const tree = setupComponentForTesting(<DomainSettings />,
    {
      console: {
        loading: false,
        activeInstance: {
          data: {
            id: 1,
            instanceName: "test",
            subdomain: "test",
            draftThemeConfig: {
              version: 1,
              mainColor: "#444444",
              linkColor: "#FFAAFF"
            },
            draftStaticContentOverrides: {
              homepageOverlayHtml: "Test overlay",
            }
          },
          feedback: {},
          loading: [],
          deployment: null,
        },
        instances: [{
          id: 1,
          instanceName: "test",
          subdomain: "test",
        }]
      }
    }).toJSON();
  expect(tree).toMatchSnapshot();
});

it('renders correctly if external domain is present', () => {
  const tree = setupComponentForTesting(<DomainSettings />,
    {
      console: {
        loading: false,
        activeInstance: {
          data: {
            id: 1,
            instanceName: "test",
            externalDomain: 'example.com',
            subdomain: "test",
            dnsConfigurationState: 'verified',
            draftThemeConfig: {
              version: 1,
              mainColor: "#444444",
              linkColor: "#FFAAFF"
            },
            draftStaticContentOverrides: {
              homepageOverlayHtml: "Test overlay",
            }
          },
          feedback: {},
          loading: [],
          deployment: null,
        },
        instances: [{
          id: 1,
          instanceName: "test",
          subdomain: "test",
        }]
      }
    }).toJSON();
  expect(tree).toMatchSnapshot();
});