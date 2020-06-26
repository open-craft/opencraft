import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { ComponentsDemo } from './ComponentsDemo';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<ComponentsDemo />).toJSON();
    expect(tree).toMatchSnapshot();
});
