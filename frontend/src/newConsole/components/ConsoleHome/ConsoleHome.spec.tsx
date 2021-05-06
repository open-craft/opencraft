import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { ConsoleHome } from './ConsoleHome';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<ConsoleHome />).toJSON();
    expect(tree).toMatchSnapshot();
});
