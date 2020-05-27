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
