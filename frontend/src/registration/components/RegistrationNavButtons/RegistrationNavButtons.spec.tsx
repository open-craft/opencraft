import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { RegistrationNavButtons } from './RegistrationNavButtons';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<RegistrationNavButtons />).toJSON();
    expect(tree).toMatchSnapshot();
});
