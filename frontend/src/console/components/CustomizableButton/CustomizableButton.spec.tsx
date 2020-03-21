import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { CustomizableButton } from './CustomizableButton';
import {act} from "react-test-renderer";

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<CustomizableButton />).toJSON();
    expect(tree).toMatchSnapshot();
});

it('changes style on hover', () => {
    const node = setupComponentForTesting(
      <CustomizableButton
        initialTextColor="#FFFFFF"
        initialBackgroundColor="#FFFFFF"
        initialBorderColor="#FFFFFF"
        initialHoverBackgroundColor="#000000"
        initialHoverTextColor="#000000"
        initialHoverBorderColor="#000000"
      />);
    act(() => {
        node.root.findByType('button').props.onMouseEnter();
    });
    const tree = node.toJSON();
    expect(tree).toMatchSnapshot();
});
