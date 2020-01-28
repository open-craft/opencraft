import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { InstanceSettings } from './InstanceSettings';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<InstanceSettings />).toJSON();
    expect(tree).toMatchSnapshot();
});
