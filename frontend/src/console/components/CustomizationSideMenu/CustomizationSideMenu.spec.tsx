import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { CustomizationSideMenu } from './CustomizationSideMenu';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<CustomizationSideMenu />).toJSON();
    expect(tree).toMatchSnapshot();
});
