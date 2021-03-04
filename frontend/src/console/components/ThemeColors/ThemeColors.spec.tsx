import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { ThemeColors } from './ThemeColors';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<ThemeColors />).toJSON();
    expect(tree).toMatchSnapshot();
});
