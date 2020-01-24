import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { LoginPage } from './LoginPage';

describe("Login Page", function() {
  it('renders without crashing', () => {
    const tree = setupComponentForTesting(<LoginPage />).toJSON();
    expect(tree).toMatchSnapshot();
  });

  it('renders error messages', () => {
    const tree = setupComponentForTesting(
      <LoginPage />,
      {
        loginState: {
          error: "Login error!"
        }
      }
    ).toJSON();
    expect(tree).toMatchSnapshot();
  });

  it('disables login button when loading login', () => {
    const tree = setupComponentForTesting(
      <LoginPage />,
      {
        loginState: {
          loading: true
        }
      }
    ).toJSON();
    expect(tree).toMatchSnapshot();
  });
});
