import * as React from 'react';

import { Redirect, Route, Switch } from 'react-router';
import { ROUTES } from '../global/constants';
import { RegistrationContainer } from '../registration/components';

export const MainRoutes = () => (
  <Switch>
    <Redirect from="/" to={ROUTES.Registration.HOME} exact />
    <Route path={ROUTES.Registration.HOME} component={RegistrationContainer} />
  </Switch>
);
