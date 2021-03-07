import React from 'react';
import {
    setupComponentForTesting,
    mountComponentForTesting,
  } from 'utils/testing';
import { RegistrationNavButtons } from './RegistrationNavButtons';


describe('Registration Navigation Buttons', function () {
    it('render without crashing', () => {
        const tree = setupComponentForTesting(<RegistrationNavButtons />).toJSON();
        expect(tree).toMatchSnapshot();
    });

    it('render spinner when loading', () => {
        const tree = setupComponentForTesting(<RegistrationNavButtons loading={true} />).toJSON();
        expect(tree).toMatchSnapshot();
    });

    it('call handleBackClick when not loading', () => {
      const mock = jest.fn();
      const tree = mountComponentForTesting(
          <RegistrationNavButtons
          loading={false}
          handleBackClick={mock}
          />,
      );
      const mountedComponent = tree.find('RegistrationNavButtons')
      const backButton = mountedComponent.find('Button.float-left')
      backButton.simulate("click");
      expect(mock).toBeCalled();
    });

    it('call handleNextClick when not loading', () => {
      const mock = jest.fn();
      const tree = mountComponentForTesting(
          <RegistrationNavButtons
          loading={false}
          handleNextClick={mock}
          />,
      );
      const mountedComponent = tree.find('RegistrationNavButtons')
      const nextButton = mountedComponent.find('Button.float-right')
      nextButton.simulate("click");
      expect(mock).toBeCalled();
    });

    it('don\'t call handleNextClick when loading', () => {
      const mock = jest.fn();
      const tree = mountComponentForTesting(
          <RegistrationNavButtons
          loading={true}
          handleNextClick={mock}
          />,
      );
      const mountedComponent = tree.find('RegistrationNavButtons')
      const nextButton = mountedComponent.find('Button.float-right')
      nextButton.simulate("click");
      expect(mock).not.toBeCalled();
    });
  })
