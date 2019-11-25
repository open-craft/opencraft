import React from 'react';
import { setupComponentForTesting } from 'utils/testing';
import { Footer } from './Footer';

it('renders without crashing', () => {
  const tree = setupComponentForTesting(<Footer />).toJSON();
  expect(tree).toMatchSnapshot();
});
