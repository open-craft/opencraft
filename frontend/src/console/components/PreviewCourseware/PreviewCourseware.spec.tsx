import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { PreviewCourseware } from './PreviewCourseware';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<PreviewCourseware />).toJSON();
    expect(tree).toMatchSnapshot();
});
