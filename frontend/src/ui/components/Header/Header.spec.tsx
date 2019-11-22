import React from 'react';
import { setupComponentForTesting } from 'utils/testing';
import { Header } from './Header';

it('renders without crashing', () => {
  const tree = setupComponentForTesting(<Header />).toJSON();
  expect(tree).toMatchSnapshot();
});
