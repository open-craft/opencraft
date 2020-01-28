import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { ConsoleContainer } from './ConsoleContainer';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<ConsoleContainer />).toJSON();
    expect(tree).toMatchSnapshot();
});
