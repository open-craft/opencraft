import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { ErrorPage } from './ErrorPage';

it('renders with default message', () => {
    const tree = setupComponentForTesting(<ErrorPage />).toJSON();
    expect(tree).toMatchSnapshot();
});

it('renders with custom message', () => {
    const testMessages = {
        testError: {
            defaultMessage: 'Test Error Message',
            description: ''
        }
    }
    const tree = setupComponentForTesting(
        <ErrorPage
            messages={testMessages}
            messageId="testError"
        />
    ).toJSON();
    expect(tree).toMatchSnapshot();
});
