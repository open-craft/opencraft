import React from 'react';
import { setupComponentForTesting } from 'utils/testing';
import { Main } from './Main';

it('renders without crashing', () => {
  const tree = setupComponentForTesting(<Main />).toJSON();
  expect(tree).toMatchSnapshot();
});
