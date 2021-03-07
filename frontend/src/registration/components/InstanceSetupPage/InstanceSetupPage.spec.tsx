import React from 'react';
import {
  setupComponentForTesting,
  mountComponentForTesting
} from 'utils/testing';
import { InstanceSetupPage } from './InstanceSetupPage';

describe('RedirectToCorrect Step component', function () {

  it('renders without crashing', () => {
    const tree = setupComponentForTesting(<InstanceSetupPage />).toJSON();
    expect(tree).toMatchSnapshot();
  });

  it('updates state with form text input contents', () => {
    const tree = mountComponentForTesting(
      <InstanceSetupPage />
    );

    const event = { target: { name: 'instanceName', value: 'some-instance' } }
    const input = tree.find({name: 'instanceName'}).at(1);
    input.simulate('change', event)
    const mountedComponent = tree.find('InstanceSetupPage')
    expect(mountedComponent.state().instanceName).toBe('some-instance')
  });
})
