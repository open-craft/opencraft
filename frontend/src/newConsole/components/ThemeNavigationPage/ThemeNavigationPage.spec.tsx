import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { ThemeNavigationPage } from './ThemeNavigationPage';

it('renders without crashing', () => {
  const tree = setupComponentForTesting(
    <ThemeNavigationPage />,
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
          loading: ['draftThemeConfig'],
          deployment: null,
        },
        instances: [{
          id: 1,
          instanceName: "test",
          subdomain: "test",
        }],
        history: {
          goBack: () => { }
        }
      }
    }).toJSON();
  expect(tree).toMatchSnapshot();
});
