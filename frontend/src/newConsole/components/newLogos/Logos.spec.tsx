import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { Logos } from './Logos';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<Logos />).toJSON();
    expect(tree).toMatchSnapshot();
});
