import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { AccountSetupPage } from './AccountSetupPage';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<AccountSetupPage />).toJSON();
    expect(tree).toMatchSnapshot();
});
