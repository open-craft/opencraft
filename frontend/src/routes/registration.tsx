import { ROUTES } from 'global/constants';
import * as React from 'react';

import { Redirect, Route, Switch } from 'react-router';
import { DomainInputPage, InstanceSetupPage } from 'registration/components';

export const RegistrationRoutes = () => (
  <Switch>
    <Route exact path={ROUTES.Registration.HOME}>
      <Redirect to={ROUTES.Registration.DOMAIN} />
    </Route>
    <Route path={ROUTES.Registration.DOMAIN} component={DomainInputPage} />
    <Route path={ROUTES.Registration.INSTANCE} component={InstanceSetupPage} />
  </Switch>
);
