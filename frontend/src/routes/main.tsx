import * as React from 'react';

import { Redirect, Route, Switch } from 'react-router';
import { ErrorPage } from 'ui/components';
import { LoginPage } from 'auth/components';
import { ROUTES } from '../global/constants';
import { RegistrationContainer } from 'registration/components';
import { ConsoleContainer } from 'console/components';

export const MainRoutes = () => (
  <Switch>
    <Redirect from="/" to={ROUTES.Registration.HOME} exact />
    <Route path="/error" component={ErrorPage} />
    <Route path="/login" component={LoginPage} />
    <Route path={ROUTES.Registration.HOME} component={RegistrationContainer} />
    <Route path={ROUTES.Console.HOME} component={ConsoleContainer} />
  </Switch>
);
