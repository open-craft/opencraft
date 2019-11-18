import { RegistrationSteps } from "global/constants";
import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { RegistrationContainer } from './RegistrationContainer';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(
        <RegistrationContainer step={RegistrationSteps.THEME} submitRegistration={jest.fn()}/>
    ).toJSON();
    expect(tree).toMatchSnapshot();
});
