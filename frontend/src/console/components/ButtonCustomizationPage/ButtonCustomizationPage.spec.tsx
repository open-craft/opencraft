import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { ButtonCustomizationPage } from './ButtonCustomizationPage';
import messages from "../ThemeButtons/displayMessages";

it('renders without crashing', () => {
    const tree = setupComponentForTesting(
      <ButtonCustomizationPage
        buttonName="Primary"
        externalMessages={messages}
        onChangeColor={() => {}}
        loading={['draftThemeConfig']}
        themeData={{}}
      />
      ).toJSON();
    expect(tree).toMatchSnapshot();
});
