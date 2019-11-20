import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { InstitutionalAccountHero } from './InstitutionalAccountHero';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<InstitutionalAccountHero />).toJSON();
    expect(tree).toMatchSnapshot();
});
