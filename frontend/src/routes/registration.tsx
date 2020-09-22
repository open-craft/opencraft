import { ROUTES } from 'global/constants';
import * as React from 'react';

import { Redirect, Route, Switch } from 'react-router';
import {
  AccountSetupPage,
  CongratulationsPage,
  DomainInputPage,
  InstanceSetupPage
  // CustomDomainSetupPage
} from 'registration/components';

export const RegistrationRoutes = () => (
  <Switch>
    <Route exact path={ROUTES.Registration.HOME}>
      <Redirect to={ROUTES.Registration.DOMAIN} />
    </Route>
    <Route path={ROUTES.Registration.DOMAIN} component={DomainInputPage} />
    <Route path={ROUTES.Registration.INSTANCE} component={InstanceSetupPage} />
    <Route path={ROUTES.Registration.ACCOUNT} component={AccountSetupPage} />
    {/* <Route
      path={ROUTES.Registration.CUSTOM_DOMAIN}
      component={CustomDomainSetupPage}
    /> */}
    <Route
      path={ROUTES.Registration.CONGRATS}
      component={CongratulationsPage}
    />
  </Switch>
);
