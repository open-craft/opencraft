import React from 'react';
import { setupComponentForTesting } from 'utils/testing';
import { InstanceSetupPage } from './InstanceSetupPage';

it('renders without crashing', () => {
  const tree = setupComponentForTesting(<InstanceSetupPage />).toJSON();
  expect(tree).toMatchSnapshot();
});
