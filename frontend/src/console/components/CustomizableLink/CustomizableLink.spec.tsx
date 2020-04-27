import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { CustomizableLink } from './CustomizableLink';
import {act} from "react-test-renderer";

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<CustomizableLink />).toJSON();
    expect(tree).toMatchSnapshot();
});

it('has the colors set properly', () => {
    const tree = setupComponentForTesting(
      <CustomizableLink
        linkColor="#FFFFFF"
        borderBottomColor="#FFFFFF"
        borderBottomHoverColor="#000000"
      />).toJSON();
    expect(tree).toMatchSnapshot();
});

it('has the "active" border', () => {
    const tree = setupComponentForTesting(
      <CustomizableLink
        linkColor="#FFFFFF"
        borderBottomColor="#FFFFFF"
        borderBottomHoverColor="#000000"
        active
      />).toJSON();
    expect(tree).toMatchSnapshot();
});

it('changes the border color on hover', () => {
    const node = setupComponentForTesting(
      <CustomizableLink
        linkColor="#FFFFFF"
        borderBottomColor="#FFFFFF"
        borderBottomHoverColor="#000000"
      />);
    act(() => {
        node.root.findByType('button').props.onMouseEnter();
    });
    const tree = node.toJSON();
    expect(tree).toMatchSnapshot();
});

it('changes the "active" border color on hover', () => {
    const node = setupComponentForTesting(
      <CustomizableLink
        linkColor="#FFFFFF"
        borderBottomColor="#FFFFFF"
        borderBottomHoverColor="#000000"
        active
      />);
    act(() => {
        node.root.findByType('button').props.onMouseEnter();
    });
    const tree = node.toJSON();
    expect(tree).toMatchSnapshot();
});

it('does not have a border with "noHover" option', () => {
    const node = setupComponentForTesting(
      <CustomizableLink
        linkColor="#FFFFFF"
        borderBottomColor="#FFFFFF"
        borderBottomHoverColor="#000000"
        noHover
      />);
    act(() => {
        node.root.findByType('button').props.onMouseEnter();
    });
    const tree = node.toJSON();
    expect(tree).toMatchSnapshot();
});
