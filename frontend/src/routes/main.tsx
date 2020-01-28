import * as React from 'react';

import { Redirect, Route, Switch } from 'react-router';
import { ErrorPage } from 'ui/components';
import { LoginPage, LogoutPage } from 'auth/components';
import { RegistrationContainer } from 'registration/components';
import { ConsoleContainer } from 'console/components';
import { ROUTES } from '../global/constants';

export const MainRoutes = () => (
  <Switch>
    <Redirect from="/" to={ROUTES.Registration.HOME} exact />
    <Route path="/error" component={ErrorPage} />
    <Route path="/login" component={LoginPage} />
    <Route path="/logout" component={LogoutPage} />
    <Route path={ROUTES.Registration.HOME} component={RegistrationContainer} />
    <Route path={ROUTES.Console.HOME} component={ConsoleContainer} />
  </Switch>
);
