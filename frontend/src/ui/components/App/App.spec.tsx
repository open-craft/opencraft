import React from 'react';
import { setupComponentForTesting } from 'utils/testing';
import { App } from './App';

it('renders without crashing', () => {
  const tree = setupComponentForTesting(<App />).toJSON();
  expect(tree).toMatchSnapshot();
});
