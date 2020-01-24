import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { LogoutPage } from './LogoutPage';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<LogoutPage />).toJSON();
    expect(tree).toMatchSnapshot();
});
