import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { ThemePreview } from './ThemePreview';


describe("Theme preview page", function() {
  it('renders without crashing', () => {
      const tree = setupComponentForTesting(<ThemePreview />).toJSON();
      expect(tree).toMatchSnapshot();
  });

  it('Render theme settings page when instance has no theme set up.', () => {
      const tree = setupComponentForTesting(
        <ThemePreview />,
        {
          console: {
            loading: false,
            activeInstance: {
              data: {
                id: 1,
                instanceName: "test",
                subdomain: "test",
                draftThemeConfig: {},
                draftStaticContentOverrides: {
                  homepageOverlayHtml: "",
                }
              },
              deployment: {
                status: "NO_STATUS",
                undeployedChanges: [],
                deployedChanges: null,
                deploymentType: 'admin',
              }
            },
            instances: [{
              id: 1,
              instanceName: "test",
              subdomain: "test",
            }]
          }
        }
      ).toJSON();
      expect(tree).toMatchSnapshot();
  });
});
