import React from 'react';
import { setupComponentForTesting } from 'utils/testing';
import { DomainInputPage } from './DomainInputPage';

describe("Domain Input Page", function() {
  it('Correctly renders domain input page', () => {
      const tree = setupComponentForTesting(
        <DomainInputPage />,
        {
          registration: {
            registrationData: {
              subdomain: 'test-subdomain',
              externalDomain: ''
            },
            registrationFeedback: {}
          }
        }
      ).toJSON();
      expect(tree).toMatchSnapshot();
  });

  it('Correctly renders domain input with error fedback', () => {
      const tree = setupComponentForTesting(
        <DomainInputPage />,
        {
          registration: {
            registrationData: {
              subdomain: 'test-subdomain',
              externalDomain: ''
            },
            registrationFeedback: {
              subdomain: ['subdomain test error']
            }
          }
        }
      ).toJSON();
      expect(tree).toMatchSnapshot();
  });

  it('Correctly goes to custom domain page and back', () => {
      let component = setupComponentForTesting(
        <DomainInputPage />,
        {
          registration: {
            registrationData: {
              subdomain: 'test-subdomain',
              externalDomain: ''
            },
            registrationFeedback: {}
          }
        }
      )

      let tree = component.toJSON();
      expect(tree).toMatchSnapshot();
  });
});
