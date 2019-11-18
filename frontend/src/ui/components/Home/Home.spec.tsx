import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { Home } from './Home';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<Home/>).toJSON();
    expect(tree).toMatchSnapshot();
});
