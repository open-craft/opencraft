import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { ButtonStyles } from './ButtonStyles';

it('renders without crashing', () => {
  const tree = setupComponentForTesting(
    <ButtonStyles
      buttonName="Primary"
      onChangeColor={() => {}}
      loading={['draftThemeConfig']}
      themeData={{}}
    />).toJSON();
    expect(tree).toMatchSnapshot();
});
