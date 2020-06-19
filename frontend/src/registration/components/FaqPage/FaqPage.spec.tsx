import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { FaqPage } from './FaqPage';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<FaqPage />).toJSON();
    expect(tree).toMatchSnapshot();
});
