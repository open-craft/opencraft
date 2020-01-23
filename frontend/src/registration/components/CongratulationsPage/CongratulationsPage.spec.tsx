import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { CongratulationsPage } from './CongratulationsPage';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<CongratulationsPage />).toJSON();
    expect(tree).toMatchSnapshot();
});
