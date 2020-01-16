import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { ConsolePage } from './ConsolePage';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<ConsolePage />).toJSON();
    expect(tree).toMatchSnapshot();
});
