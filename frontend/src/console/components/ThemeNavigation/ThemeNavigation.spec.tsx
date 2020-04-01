import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { ThemeNavigation } from './ThemeNavigation';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<ThemeNavigation />).toJSON();
    expect(tree).toMatchSnapshot();
});
