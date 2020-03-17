import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { CustomizableButton } from './CustomizableButton';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<CustomizableButton />).toJSON();
    expect(tree).toMatchSnapshot();
});
