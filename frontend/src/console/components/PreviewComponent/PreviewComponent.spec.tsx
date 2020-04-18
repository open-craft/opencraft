import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { PreviewComponent } from './PreviewComponent';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<PreviewComponent instanceData={{}} themeData={{}}/>).toJSON();
    expect(tree).toMatchSnapshot();
});
