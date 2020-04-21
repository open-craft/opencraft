import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { ThemeFooter } from './ThemeFooter';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<ThemeFooter />).toJSON();
    expect(tree).toMatchSnapshot();
});
