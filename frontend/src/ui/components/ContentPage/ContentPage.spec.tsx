import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { ContentPage } from './ContentPage';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<ContentPage />).toJSON();
    expect(tree).toMatchSnapshot();
});
