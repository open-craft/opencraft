import React from 'react';
import { RedirectToCorrectStep } from "./RedirectToCorrectStep";
import {
    setupComponentForTesting,
    mountComponentForTesting,
  } from 'utils/testing';
import {
    ROUTES,
    REGISTRATION_STEPS,
  } from 'global/constants';



describe('RedirectToCorrect Step component', function () {
    it('renders without crashing', () => {
        const tree = setupComponentForTesting(<RedirectToCorrectStep />).toJSON();
        expect(tree).toMatchSnapshot();
    });

    it('redirects to currentRegistrationStep if currentPageStep > currentRegistrationStep', () => {
        const tree = mountComponentForTesting(
            <RedirectToCorrectStep
                currentPageStep={1}
                currentRegistrationStep={0}
            />
        );
        const mountedComponent = tree.find('RedirectToCorrectStep')
        expect(
            mountedComponent.prop('currentPageStep')
        ).toBeGreaterThan(
            mountedComponent.prop('currentRegistrationStep')
        )
        expect(mountedComponent.find('Redirect').prop('to')).toBe(REGISTRATION_STEPS[0]);
    });

    // The following tests check RedirectToCorrectStep's behavior
    // Every router dispatch for /registration updates currentRegistrationStep
    // so we want RedirectToCorrectStep's 'to' prop and Redirect child
    // to fit in with the registration flow logic.

    it('redirects to currentRegistrationStep if currentPageStep > currentRegistrationStep', () => {
        const tree = mountComponentForTesting(
            <RedirectToCorrectStep
                currentPageStep={1}
                currentRegistrationStep={0}
            />
        );
        const mountedComponent = tree.find('Redirect')
        expect(mountedComponent.prop('to')).toBe(REGISTRATION_STEPS[0]);
    });

    it('renders null if currentPageStep <= currentRegistrationStep', () => {
        const tree = mountComponentForTesting(
            <RedirectToCorrectStep
                currentPageStep={0}
                currentRegistrationStep={1}
            />
        );
        expect(tree).not.toContain('Redirect');
    });

    it('redirects to /congrats if currentPageStep = ROUTES.Registration.CONGRATS', () => {
        const tree = mountComponentForTesting(
            <RedirectToCorrectStep
                currentPageStep={4}
                currentRegistrationStep={4}
            />
        );
        const mountedComponent = tree.find('Redirect')
        expect(mountedComponent.prop('to')).toBe(ROUTES.Registration.CONGRATS);
    });
  })
