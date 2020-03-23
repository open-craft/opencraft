import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { ImageUploadField } from './ImageUploadField';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<ImageUploadField />).toJSON();
    expect(tree).toMatchSnapshot();
});
