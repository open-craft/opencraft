import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { ThemePreviewAndColors } from './ThemePreviewAndColors';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<ThemePreviewAndColors />).toJSON();
    expect(tree).toMatchSnapshot();
});
