import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { AddDomainButton } from './AddDomainModalButton';

it('renders without crashing', () => {
  const tree = setupComponentForTesting(
    <AddDomainButton />,
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
          feedback: [],
          loading: ['draftThemeConfig'],
          deployment: null,
        },
      }
    }
  ).toJSON();
  expect(tree).toMatchSnapshot();
});

it('renders null when externalDomain in data', () => {
  const tree = setupComponentForTesting(
    <AddDomainButton />,
    {
      console: {
        loading: false,
        activeInstance: {
          data: {
            id: 1,
            instanceName: "test",
            externalDomain: 'example.com',
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
          feedback: [],
          loading: ['draftThemeConfig'],
          deployment: null,
        },
      }
    }
  ).toJSON();
  expect(tree).toMatchSnapshot();
})
