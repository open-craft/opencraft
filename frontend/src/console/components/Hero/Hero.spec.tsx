import React from 'react';
import {setupComponentForTesting} from "utils/testing";
import {Hero} from './Hero';


describe('Hero customization page', function () {
  it('renders without crashing', () => {
    const tree = setupComponentForTesting(<Hero/>).toJSON();
    expect(tree).toMatchSnapshot();
  });

  it('renders the hero customization page when instance all its dependencies are set up', () => {
    const tree = setupComponentForTesting(
      <Hero/>,
      {
        console: {
          loading: false,
          activeInstance: {
            data: {
              id: 1,
              instanceName: "test",
              subdomain: "test",
              heroCoverImage: "https://example.com/cover.png",
              draftThemeConfig: {
                homePageHeroTitleColor: '#000',
                homePageHeroSubtitleColor: '#999'
              },
              draftStaticContentOverrides: {
                homepageOverlayHtml: "<h1>Welcome to My Instance</h1><p>It works! Powered by Open edX®</p>"
              }
            },
            deployment: null
          },
          instances: [{
            id: 1,
            instanceName: "test",
            subdomain: "test"
          }]
        }
      }
    ).toJSON();
    expect(tree).toMatchSnapshot();
  });

  it('renders the hero customization page when instance does not have the theme set up', () => {
    const tree = setupComponentForTesting(
      <Hero/>,
      {
        console: {
          loading: false,
          activeInstance: {
            data: {
              id: 1,
              instanceName: "test",
              subdomain: "test",
              draftThemeConfig: {}
            },
            deployment: null,
          },
          instances: [{
            id: 1,
            instanceName: "test",
            subdomain: "test"
          }]
        }
      }
    ).toJSON();
    expect(tree).toMatchSnapshot();
  });
  it(
    'renders the hero customization page when the instance does not have the static content overrides set up',
    () => {
      const tree = setupComponentForTesting(
        <Hero/>,
        {
          console: {
            loading: false,
            activeInstance: {
              data: {
                id: 1,
                instanceName: "test",
                subdomain: "test",
                heroCoverImage: "https://example.com/cover.png",
                draftThemeConfig: {
                  homePageHeroTitleColor: '#000',
                  homePageHeroSubtitleColor: '#999'
                },
                draftStaticContentOverrides: {
                  homepageOverlayHtml: "<h1>Welcome to My Instance</h1><p>It works! Powered by Open edX®</p>"
                }
              },
              deployment: null,
            },
            instances: [{
              id: 1,
              instanceName: "test",
              subdomain: "test"
            }]
          }
        }
      ).toJSON();
      expect(tree).toMatchSnapshot();
    });

  it(
    'renders the hero customization page when the instance does not have the cover image set up',
    () => {
      const tree = setupComponentForTesting(
        <Hero/>,
        {
          console: {
            loading: false,
            activeInstance: {
              data: {
                id: 1,
                instanceName: "test",
                subdomain: "test",
                draftThemeConfig: {
                  homePageHeroTitleColor: '#000',
                  homePageHeroSubtitleColor: '#999'
                },
                draftStaticContentOverrides: {
                  homepageOverlayHtml: "<h1>Welcome to My Instance</h1><p>It works! Powered by Open edX®</p>"
                }
              },
              deployment: null,
            },
            instances: [{
              id: 1,
              instanceName: "test",
              subdomain: "test"
            }]
          }
        }
      ).toJSON();
      expect(tree).toMatchSnapshot();
    });
});
