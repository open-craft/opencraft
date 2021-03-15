import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { PreviewDashboard } from './PreviewDashboard';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<PreviewDashboard />).toJSON();
    expect(tree).toMatchSnapshot();
});
