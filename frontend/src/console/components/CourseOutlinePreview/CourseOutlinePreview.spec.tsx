import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { CourseOutlinePreview } from './CourseOutlinePreview';

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
    const tree = setupComponentForTesting(<CourseOutlinePreview instanceData={instanceData} />).toJSON();
    expect(tree).toMatchSnapshot();
});
