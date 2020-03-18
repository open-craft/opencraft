import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { TextInputField } from './TextInputField';

const messages = {
  test: {
    defaultMessage: 'A translatable string.',
    description: ''
  },
  testHelp: {
    defaultMessage: 'A translatable string.',
    description: ''
  }
};


it('renders without crashing', () => {
    const tree = setupComponentForTesting(
      <TextInputField
        fieldName="test"
        value="test"
        type="password"
        error="test"
        onChange={() => {}}
        messages={messages}
      />
    ).toJSON();
    expect(tree).toMatchSnapshot();
});
