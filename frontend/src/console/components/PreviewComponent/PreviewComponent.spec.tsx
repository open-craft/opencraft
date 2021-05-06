import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { PreviewComponent } from './PreviewComponent';

describe('PreviewComponent', function() {
  it('renders without crashing when preview prop is not set', () => {
      const instanceData = {
          id: 1,
          instanceName: "test",
          subdomain: "test",
          publicContactEmail: "",
          privacyPolicyUrl: "",
          draftThemeConfig: {},
          draftStaticContentOverrides: {
            homepageOverlayHtml: "",
          },
          heroCoverImage: "test",
          staticPagesEnabled: {
            "Dummy": "value"
          }
      }
      const tree = setupComponentForTesting(
        <PreviewComponent
          instanceData={instanceData}
        />).toJSON();
      expect(tree).toMatchSnapshot();
  });

  it('renders dashboard preview when preview prop is set', () => {
    const instanceData = {
        id: 1,
        instanceName: "test",
        subdomain: "test",
        publicContactEmail: "",
        privacyPolicyUrl: "",
        draftThemeConfig: {},
        draftStaticContentOverrides: {
          homepageOverlayHtml: "",
        },
        heroCoverImage: "test",
        staticPagesEnabled: {
          "Dummy": "value"
        }
    };
    const tree = setupComponentForTesting(
    <PreviewComponent
      instanceData={instanceData}
      currentPreview={'dashboard'}
    />).toJSON();
    expect(tree).toMatchSnapshot();
  });

});
