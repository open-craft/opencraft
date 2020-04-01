import * as React from 'react';

import { Switch, Route, Redirect } from 'react-router';
import {
  InstanceSettings,
  Logos,
  ThemeButtons,
  ThemeNavigation,
  ThemeFooter,
  ThemePreviewAndColors
} from 'console/components';
import { PrivateRoute } from 'auth/components';
import { ROUTES } from '../global/constants';

export const ConsoleRoutes = () => {
  return (
    <Switch>
      // Redirect to main customization page
      <Route exact path={ROUTES.Console.HOME}>
        <Redirect to={ROUTES.Console.INSTANCE_SETTINGS_GENERAL} />
      </Route>
      <PrivateRoute
        path={ROUTES.Console.INSTANCE_SETTINGS_GENERAL}
        component={InstanceSettings}
      />
      <PrivateRoute
        path={ROUTES.Console.THEME_PREVIEW_AND_COLORS}
        component={ThemePreviewAndColors}
      />
      <PrivateRoute
        path={ROUTES.Console.THEME_BUTTONS}
        component={ThemeButtons}
      />
      <PrivateRoute
        path={ROUTES.Console.THEME_NAVIGATION}
        component={ThemeNavigation}
      />
      <PrivateRoute
        path={ROUTES.Console.THEME_FOOTER}
        component={ThemeFooter}
      />
      <PrivateRoute path={ROUTES.Console.LOGOS} component={Logos} />
    </Switch>
  );
};
