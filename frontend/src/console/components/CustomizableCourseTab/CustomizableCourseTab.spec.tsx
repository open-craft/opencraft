import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { CustomizableCourseTab } from './CustomizableCourseTab';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<CustomizableCourseTab color="#f30000" />).toJSON();
    expect(tree).toMatchSnapshot();
});
