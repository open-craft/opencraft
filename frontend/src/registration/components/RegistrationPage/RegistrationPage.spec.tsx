import React from 'react';
import {
  setupComponentForTesting,
  mountComponentForTesting,
} from 'utils/testing';
import { RegistrationPage } from './RegistrationPage';


describe('Registration page', function () {
  it('renders without crashing', () => {
    const tree = setupComponentForTesting(<RegistrationPage />).toJSON();
    expect(tree).toMatchSnapshot();
  });

  it('renders with props set up', () => {
    const tree = mountComponentForTesting(
      <RegistrationPage
        title={'test-title'}
        subtitleBig={'test-subtitleBig'}
        subtitle={'test-subtitle'}
        children={'test-child'}
        currentStep={0}
      />,
    );
    const mountedComponent = tree.find('RegistrationPage')

    expect(mountedComponent.find('h1').at(0).text()).toBe('test-title');
    expect(mountedComponent.find('h1').at(1).text()).toBe('test-subtitleBig');
    expect(mountedComponent.find('h2').text()).toBe('test-subtitle');
    expect(mountedComponent.find('StepBar').at(0).prop('currentStep')).toBe(0);
    expect(mountedComponent.find('div.registration-page-content').text()).toBe('test-child')
  });

  it('still renders vital components when subtitles are missing', () => {
    const tree = mountComponentForTesting(
      <RegistrationPage
        title={'test-title'}
        children={'test-child'}
        currentStep={0}
      />,
    );
    const mountedComponent = tree.find('RegistrationPage')

    expect(mountedComponent.find('h1').text()).toBe('test-title');
    expect(mountedComponent.find('StepBar').at(0).prop('currentStep')).toBe(0);
    expect(mountedComponent.find('div.registration-page-content').text()).toBe('test-child')
  });
})
