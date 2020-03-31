import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { ToggleSwitch } from './ToggleSwitch';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<ToggleSwitch  fieldName='test'/>).toJSON();
    expect(tree).toMatchSnapshot();
});
