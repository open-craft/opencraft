import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { EmailVerificationPage } from './EmailVerificationPage';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<EmailVerificationPage />).toJSON();
    expect(tree).toMatchSnapshot();
});
