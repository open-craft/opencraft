import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { CoursesListingItem } from './CoursesListingItem';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<CoursesListingItem  themeData={{}}/>).toJSON();
    expect(tree).toMatchSnapshot();
});
