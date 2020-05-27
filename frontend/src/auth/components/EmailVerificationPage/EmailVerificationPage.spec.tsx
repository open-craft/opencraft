import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { EmailVerificationPage } from './EmailVerificationPage';


describe("Email verification page", function() {
  const mockTokenProps = {
    params: {
      id: "verification_token"
    }
  }

  it('renders loading page', () => {
    const tree = setupComponentForTesting(
      <EmailVerificationPage
        match={mockTokenProps}
        loading={true}
      />,
    ).toJSON();

    expect(tree).toMatchSnapshot();
  });

  it('renders the confirmed email verification page', () => {
    const tree = setupComponentForTesting(
      <EmailVerificationPage
        match={mockTokenProps}
        loading={false}
        succeeded={true}
      />,
    ).toJSON();

    expect(tree).toMatchSnapshot();
  });

  it('renders the failed email verification page', () => {
    const tree = setupComponentForTesting(
      <EmailVerificationPage
        match={mockTokenProps}
        loading={false}
        succeeded={true}
      />,
    ).toJSON();

    expect(tree).toMatchSnapshot();
  });
});
