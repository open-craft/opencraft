import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { RedeploymentToolbar } from './RedeploymentToolbar';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<RedeploymentToolbar />).toJSON();
    expect(tree).toMatchSnapshot();
});
