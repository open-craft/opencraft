import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { ButtonCustomizationComponent } from './ButtonCustomizationComponent';
import messages from "../ButtonsCustomizationPage/displayMessages";

it('renders without crashing', () => {
  const tree = setupComponentForTesting(
    <ButtonCustomizationComponent 
      buttonName="Primary"
      externalMessages={messages}
      onChangeColor={() => {}}
      loading={['draftThemeConfig']}
      themeData={{}}/>).toJSON();
    expect(tree).toMatchSnapshot();
});
