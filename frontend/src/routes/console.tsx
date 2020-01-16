import * as React from 'react';

import { Switch } from 'react-router';
import { InstanceSettings } from 'console/components';
import { PrivateRoute } from 'auth/components';

export const ConsoleRoutes = () => {
  return (
    <Switch>
      <PrivateRoute
        path="/console/instance-settings"
        component={InstanceSettings}
        />
    </Switch>
  );
};
