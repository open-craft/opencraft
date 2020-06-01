import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { CustomStatusPill } from './CustomStatusPill';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<CustomStatusPill />).toJSON();
    expect(tree).toMatchSnapshot();
});
