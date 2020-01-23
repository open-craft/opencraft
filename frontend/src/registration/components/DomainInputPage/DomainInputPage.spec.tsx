import React from 'react';
import { setupComponentForTesting } from 'utils/testing';
import { DomainInputPage } from './DomainInputPage';

it('renders without crashing', () => {
  const tree = setupComponentForTesting(<DomainInputPage />).toJSON();
  expect(tree).toMatchSnapshot();
});
