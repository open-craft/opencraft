import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { PrivateRoute } from './PrivateRoute';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<PrivateRoute />).toJSON();
    expect(tree).toMatchSnapshot();
});
