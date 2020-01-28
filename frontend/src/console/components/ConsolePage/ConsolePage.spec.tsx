import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { ConsolePage } from './ConsolePage';


describe("Console Page", function() {
  it('Correctly renders loading page', () => {
      const tree = setupComponentForTesting(
        <ConsolePage contentLoading={true}>
          <span> Test! </span>
        </ConsolePage>,
        {
          console: {
            loading: true
          }
        }
      ).toJSON();
      expect(tree).toMatchSnapshot();
  });

  it('Correctly renders page with data', () => {
      const tree = setupComponentForTesting(
        <ConsolePage contentLoading={false}>
          <span> Test! </span>
        </ConsolePage>,
        {
          console: {
            loading: false,
            selectedInstance: 0,
            instances: [{
              id: 1,
              instanceName: "test",
              subdomain: "test",
            }]
          }
        }
      ).toJSON();
      expect(tree).toMatchSnapshot();
  });
});
