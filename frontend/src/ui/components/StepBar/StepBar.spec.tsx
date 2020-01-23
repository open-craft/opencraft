import React from 'react';
import { setupComponentForTesting } from 'utils/testing';
import { StepBar } from './StepBar';

it('renders without crashing', () => {
  const tree = setupComponentForTesting(<StepBar />).toJSON();
  expect(tree).toMatchSnapshot();
});
