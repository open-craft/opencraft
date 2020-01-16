import * as React from 'react';

import { Switch, Route, Redirect } from 'react-router';
import { InstanceSettings } from 'console/components';
import { PrivateRoute } from 'auth/components';
import { ROUTES } from '../global/constants';

export const ConsoleRoutes = () => {
  return (
    <Switch>
      <Route exact path={ROUTES.Console.HOME}>
        <Redirect to={ROUTES.Console.INSTANCE_SETTINGS} />
      </Route>
      <PrivateRoute
        path={ROUTES.Console.INSTANCE_SETTINGS}
        component={InstanceSettings}
      />
    </Switch>
  );
};
