import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { RedirectToCorrectStep } from './RedirectToCorrectStep';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<RedirectToCorrectStep />).toJSON();
    expect(tree).toMatchSnapshot();
});
