import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { DomainInput } from './DomainInput';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<DomainInput />).toJSON();
    expect(tree).toMatchSnapshot();
});
