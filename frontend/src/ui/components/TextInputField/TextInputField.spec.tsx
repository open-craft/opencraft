import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { TextInputField } from './TextInputField';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<TextInputField />).toJSON();
    expect(tree).toMatchSnapshot();
});
