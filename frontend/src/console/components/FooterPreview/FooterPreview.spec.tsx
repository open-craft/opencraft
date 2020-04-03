import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { FooterPreview } from './FooterPreview';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<FooterPreview instanceData={null} themeData={{}}/>).toJSON();
    expect(tree).toMatchSnapshot();
});
