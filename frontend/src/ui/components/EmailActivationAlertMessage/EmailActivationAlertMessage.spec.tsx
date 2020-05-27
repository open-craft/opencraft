import React from 'react';
import { setupComponentForTesting } from 'utils/testing';
import { EmailActivationAlertMessage } from './EmailActivationAlertMessage';

it('renders without crashing', () => {
  const tree = setupComponentForTesting(<EmailActivationAlertMessage />).toJSON();
  expect(tree).toMatchSnapshot();
});
