import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { ErrorPage } from './ErrorPage';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<ErrorPage />).toJSON();
    expect(tree).toMatchSnapshot();
});
