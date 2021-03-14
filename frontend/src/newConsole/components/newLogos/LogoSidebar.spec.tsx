import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { LogosSideBar } from './LogoSidebar';


describe("Console Page", function() {
  it('Correctly renders LogosSideBar', () => {
      const tree = setupComponentForTesting(
        <LogosSideBar
            history={()=>{}}
        />).toJSON();
      expect(tree).toMatchSnapshot();
  });
});
