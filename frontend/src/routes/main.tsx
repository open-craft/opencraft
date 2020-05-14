import * as React from 'react';

import { Redirect, Route, Switch } from 'react-router';
import { ErrorPage } from 'ui/components';
import {
  LoginPage,
  LogoutPage,
  PasswordForgottenPage,
  PasswordResetPage,
  PrivateRoute,
} from 'auth/components';
import { RegistrationContainer } from 'registration/components';
import { ConsoleContainer } from 'console/components';
import { ROUTES } from '../global/constants';

export const MainRoutes = () => (
  <Switch>
    <PrivateRoute exact path="/" ifUnauthorizedRedirectTo={ROUTES.Registration.HOME}>
      <Redirect to={ROUTES.Console.HOME} />
    </PrivateRoute>
    <Route path={ROUTES.Error.UNKNOWN_ERROR} component={ErrorPage} />
    <Route path={ROUTES.Auth.LOGIN} component={LoginPage} />
    <Route path={ROUTES.Auth.LOGOUT} component={LogoutPage} />
    <Route
      path={ROUTES.Auth.PASSWORD_FORGOTTEN}
      component={PasswordForgottenPage}
    />
    <Route path={ROUTES.Auth.PASSWORD_RESET} component={PasswordResetPage} />
    <Route path={ROUTES.Registration.HOME} component={RegistrationContainer} />
    <Route path={ROUTES.Console.HOME} component={ConsoleContainer} />
  </Switch>
);
