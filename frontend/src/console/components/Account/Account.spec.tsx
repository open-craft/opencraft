import React from 'react';
import { setupComponentForTesting } from 'utils/testing';
import { Account } from './Account'

describe('Account tests', () => {
  it('Correctly renders page without data', () => {
    const tree = setupComponentForTesting(
      <Account />,
      {
        console: {
          loading: false,
          account: {
            fullName: '',
            email: '',
            oldPassword: '',
            newPasword: ''
          },
          activeInstance: {
            data: null
          }
        }
      }
    ).toJSON();
    expect(tree).toMatchSnapshot();
  });

  it('Correctly renders page with data', () => {
    const tree = setupComponentForTesting(
      <Account />,
      {
        console: {
          loading: false,
          account: {
            fullName: 'Anon Y. Mous',
            email: 'anon@ymous.com',
            oldPassword: '',
            newPasword: ''
          },
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
});
