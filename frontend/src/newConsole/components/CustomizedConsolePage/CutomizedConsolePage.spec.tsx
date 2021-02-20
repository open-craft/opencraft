import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { CustomizedConsolePage } from './CutomizedConsolePage';


describe("Console Page", function() {
  it('Correctly renders loading page', () => {
      const tree = setupComponentForTesting(
        <CustomizedConsolePage contentLoading={true}>
          <span> Test! </span>
        </CustomizedConsolePage>,
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
        <CustomizedConsolePage contentLoading={false}>
          <span> Test! </span>
        </CustomizedConsolePage>,
        {
          console: {
            loading: false,
            activeInstance: {
              data: {
                id: 1,
                instanceName: "test",
                subdomain: "test",
                lmsUrl: "test-url",
                studioUrl: "test-url",
                isEmailVerified: true,
              },
              deployment: {
                status: "preparing",
                undeployedChanges: [],
                deployedChanges: null,
                type: 'admin',
              }
            },
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

  it('Correctly renders page with email not verified alert', () => {
    const tree = setupComponentForTesting(
      <ConsolePage contentLoading={false}>
        <span> Test! </span>
      </ConsolePage>,
      {
        console: {
          loading: false,
          activeInstance: {
            data: {
              id: 1,
              instanceName: "test",
              subdomain: "test",
              lmsUrl: "test-url",
              studioUrl: "test-url",
              isEmailVerified: false,
            },
            deployment: {
              status: "preparing",
              undeployedChanges: [],
              deployedChanges: null,
              type: 'admin',
            }
          },
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
