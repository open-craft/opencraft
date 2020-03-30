import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { CustomPages } from './CustomPages';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(
        <CustomPages />
    ).toJSON();
    expect(tree).toMatchSnapshot();
});
