import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { DomainSuccessJumbotron } from './DomainSuccessJumbotron';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<DomainSuccessJumbotron />).toJSON();
    expect(tree).toMatchSnapshot();
});
