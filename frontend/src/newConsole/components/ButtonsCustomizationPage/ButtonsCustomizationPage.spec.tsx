import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { ButtonsCustomization } from './ButtonsCustomizationPage';

it('renders without crashing', () => {
  const tree = setupComponentForTesting(
    <ButtonsCustomization />,
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
    }
  ).toJSON();
  expect(tree).toMatchSnapshot();
});
