import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { PreviewBox } from './PreviewBox';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<PreviewBox />).toJSON();
    expect(tree).toMatchSnapshot();
});
