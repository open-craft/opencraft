import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { CustomizableLink } from './CustomizableLink';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<CustomizableLink />).toJSON();
    expect(tree).toMatchSnapshot();
});
