import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { LoginPage } from './LoginPage';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<LoginPage />).toJSON();
    expect(tree).toMatchSnapshot();
});
