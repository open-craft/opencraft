import React from 'react';
import { setupComponentForTesting } from 'utils/testing';
import { RegistrationPage } from './RegistrationPage';

it('renders without crashing', () => {
  const tree = setupComponentForTesting(<RegistrationPage />).toJSON();
  expect(tree).toMatchSnapshot();
});
