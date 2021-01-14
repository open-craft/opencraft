import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { DeploymentIndicator } from './DeploymentIndicator';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<DeploymentIndicator />).toJSON();
    expect(tree).toMatchSnapshot();
});
