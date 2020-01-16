import * as React from 'react';

import { Switch } from 'react-router';
import { InstanceSettings } from 'console/components';
import { PrivateRoute } from 'auth/components';
// import { checkAuthAndRefreshToken } from 'auth/utils/helpers';

export const ConsoleRoutes = () => {
  // let isAuthenticated = checkAuthAndRefreshToken();

  return (
    <Switch>
      <PrivateRoute
        restrictedPath="/console/instance-settings"
        authenticationPath="/login"
        component={InstanceSettings}
        isAuthenticated={true}
        isAllowed
        />
    </Switch>
  );
};
