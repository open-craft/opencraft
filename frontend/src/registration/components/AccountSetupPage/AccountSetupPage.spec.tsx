import React from 'react';
import {
    setupComponentForTesting,
    mountComponentForTesting
} from "utils/testing";
import { AccountSetupPage } from './AccountSetupPage';

describe('AccountSetup page component', function () {

    it('renders without crashing', () => {
        const tree = setupComponentForTesting(<AccountSetupPage />).toJSON();
        expect(tree).toMatchSnapshot();
    });

    it('updates state with correct form input', () => {
      const tree = mountComponentForTesting(<AccountSetupPage/>);
      var nextButton = tree.find('button').at(1)
      expect(nextButton.prop('disabled')).toBe(true)

      const fullNameInput = tree.find('input').at(0);
      const usernameInput = tree.find('input').at(1);
      const emailInput = tree.find('input').at(2);
      const passwordInput = tree.find('input').at(3);
      const passwordConfirmInput = tree.find('input').at(4);
      const acceptTOSInput = tree.find('input').at(5);
      const acceptDomainConditionInput = tree.find('input').at(6);
      const subscribeToUpdatesInput = tree.find('input').at(7);

      fullNameInput.simulate('change', {
          target: {
              name:fullNameInput.prop('name'),
              value:'Some Fullname'
          }
      })
      usernameInput.simulate('change', {
          target: {
              name:usernameInput.prop('name'),
              value:'someUsername'
          }
      })
      emailInput.simulate('change', {
          target: {
              name:emailInput.prop('name'),
              value:'some@email.com'
          }
      })
      passwordInput.simulate('change', {
          target: {
              name:passwordInput.prop('name'),
              value:'Somepassword1#'
          }
      })
      passwordConfirmInput.simulate('change', {
          target: {
              name:passwordConfirmInput.prop('name'),
              value:'Somepassword1#'
          }
      })
      acceptTOSInput.simulate('change', {
          target: {
              name:acceptTOSInput.prop('name'),
              checked:true,
              type: 'checkbox'
          }
      })
      acceptDomainConditionInput.simulate('change', {
          target: {
              name:acceptDomainConditionInput.prop('name'),
              checked:true,
              type: 'checkbox'
          }
      })
      subscribeToUpdatesInput.simulate('change', {
          target: {
              name:subscribeToUpdatesInput.prop('name'),
              checked:true,
              type: 'checkbox'
          }
      })
      const mountedComponent = tree.find('AccountSetupPage').first().instance()
      expect(mountedComponent.state).toStrictEqual({
        fullName: 'Some Fullname',
        username: 'someUsername',
        email: 'some@email.com',
        password: 'Somepassword1#',
        passwordConfirm: 'Somepassword1#',
        acceptTOS: true,
        acceptDomainCondition: true,
        subscribeToUpdates: true
      })
      nextButton = tree.find('button').at(1)
      expect(nextButton.prop('disabled')).toBe(false)

    });
})

