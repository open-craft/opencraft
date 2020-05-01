import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { PasswordResetPage } from './PasswordResetPage';

it('renders without crashing', () => {
    const mockTokenProps = {
    params: {
      token: "test_token"
    }
  }
    const tree = setupComponentForTesting(
      <PasswordResetPage
        match={mockTokenProps}
        loading={false}
        succeeded={false}
        error={''}
        clearErrorMessage={() => {}}
        performPasswordReset={() => {}}
        performPasswordResetTokenValidation={() => {}}
      />).toJSON();
    expect(tree).toMatchSnapshot();
});
