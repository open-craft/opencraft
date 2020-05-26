import React from 'react';
import { setupComponentForTesting } from 'utils/testing';
import { AlertMessage } from './AlertMessage';

it('renders without crashing', () => {
  const tree = setupComponentForTesting(<AlertMessage />).toJSON();
  expect(tree).toMatchSnapshot();
});
