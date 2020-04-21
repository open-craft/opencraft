import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { ThemeButtons } from './ThemeButtons';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<ThemeButtons />).toJSON();
    expect(tree).toMatchSnapshot();
});
