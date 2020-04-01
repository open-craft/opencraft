import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { CustomFooter } from './CustomFooter';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<CustomFooter themeData={{}}/>).toJSON();
    expect(tree).toMatchSnapshot();
});
