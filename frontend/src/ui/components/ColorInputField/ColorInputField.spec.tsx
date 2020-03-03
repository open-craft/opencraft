import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { ColorInputField } from './ColorInputField';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<ColorInputField />).toJSON();
    expect(tree).toMatchSnapshot();
});
