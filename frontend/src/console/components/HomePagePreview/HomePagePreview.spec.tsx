import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { HomePagePreview } from './HomePagePreview';

it('renders without crashing', () => {
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
    }
    const tree = setupComponentForTesting(<HomePagePreview instanceData={instanceData} />).toJSON();
    expect(tree).toMatchSnapshot();
});
