import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { CustomDomainSetupPage } from './CustomDomainSetupPage';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<CustomDomainSetupPage />).toJSON();
    expect(tree).toMatchSnapshot();
});
