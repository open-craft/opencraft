import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { ColorInputField } from './ColorInputField';
import { act } from 'react-test-renderer';

// interface ColorInputFieldProps {
//   fieldName: string;
//   initialValue?: string;
//   onChange?: any;
//   error?: string;
//   messages: any;
//   loading?: boolean;
// }

describe("ColorInputField Component", function() {
  const testMessages = {
    test: {
      defaultMessage: 'Test',
      description: ''
    },
    testHelp: {
      defaultMessage: 'Test helper',
      description: ''
    }
  }

  it('Correctly renders color input field.', () => {
      const tree = setupComponentForTesting(
        <ColorInputField
          fieldName="test"
          messages={testMessages}
        />
      ).toJSON();
      expect(tree).toMatchSnapshot();
  });

  it('Render with default value.', () => {
      const tree = setupComponentForTesting(
        <ColorInputField
          fieldName="test"
          initialValue="#FFFFFF"
          messages={testMessages}
        />
      ).toJSON();
      expect(tree).toMatchSnapshot();
  });

  it('Render loading.', () => {
      const tree = setupComponentForTesting(
        <ColorInputField
          fieldName="test"
          initialValue="#FFFFFF"
          messages={testMessages}
          loading={true}
        />
      ).toJSON();
      expect(tree).toMatchSnapshot();
  });

  it('Render component, check if color picker shows after clicking on field and vanishes after clicking outside.', () => {
      let component = setupComponentForTesting(
        <ColorInputField
          fieldName="test"
          initialValue="#FFFFFF"
          messages={testMessages}
        />
      )

      let tree = component.toJSON();
      expect(tree).toMatchSnapshot();

      // Click on field button and check if color picker was opened
      act(() => {
        component.root.findByType("input").props.onFocus({preventDefault: () => {}});
      })
      tree = component.toJSON();
      expect(tree).toMatchSnapshot();

      // Click on field button and check if color picker was opened
      act(() => {
        component.root.findByProps({className: "input-color-picker"}).props.onBlur();
      })
      tree = component.toJSON();
      expect(tree).toMatchSnapshot();
  });
});
