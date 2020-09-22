import React from 'react';
import { setupComponentForTesting } from 'utils/testing';
import { CustomDomainContactPage } from './CustomDomainContactPage';


describe("Custom Domain Contact Page", function() {
    it('Correctly renders Custom Domain Contact page', () => {
        const tree = setupComponentForTesting(
          <CustomDomainContactPage />
        ).toJSON();
        expect(tree).toMatchSnapshot();
    });
})

