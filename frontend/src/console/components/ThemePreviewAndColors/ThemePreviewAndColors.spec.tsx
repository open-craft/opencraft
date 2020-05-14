import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { ThemePreviewAndColors } from './ThemePreviewAndColors';


describe("Theme preview and colors page", function() {
  it('renders without crashing', () => {
      const tree = setupComponentForTesting(<ThemePreviewAndColors />).toJSON();
      expect(tree).toMatchSnapshot();
  });

  it('Render theme settings page when instance has no theme set up.', () => {
      const tree = setupComponentForTesting(
        <ThemePreviewAndColors />,
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

  it('Render theme settings page with theme set up.', () => {
      const tree = setupComponentForTesting(
        <ThemePreviewAndColors />,
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
              loading: [],
              deployment: null,
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

  it('Render theme settings page with theme set up, fields disabled after pushing changes.', () => {
      const tree = setupComponentForTesting(
        <ThemePreviewAndColors />,
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
            }]
          }
        }
      ).toJSON();
      expect(tree).toMatchSnapshot();
  });
});
