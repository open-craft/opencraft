import React from 'react';
import {setupComponentForTesting} from "utils/testing";
import {PasswordForgottenPage} from './PasswordForgottenPage';

it('renders without crashing', () => {
    const tree = setupComponentForTesting(
      <PasswordForgottenPage
        loading={false}
        succeeded={false}
        error={''}
        performPasswordForgotten={() => {}}
      />).toJSON();
    expect(tree).toMatchSnapshot();
});
