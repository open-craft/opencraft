import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { CollapseEditArea } from './CollapseEditArea';

describe("CollapseEditArea Component", function() {
  it('Correctly renders collapsible area.', () => {
      const tree = setupComponentForTesting(
        <CollapseEditArea>
          Test
        </CollapseEditArea>
      ).toJSON();
      expect(tree).toMatchSnapshot();
  });

  it('Correctly renders collapsible area expanded.', () => {
      const tree = setupComponentForTesting(
        <CollapseEditArea initialExpanded={true}>
          Test
        </CollapseEditArea>
      ).toJSON();
      expect(tree).toMatchSnapshot();
  });
});
