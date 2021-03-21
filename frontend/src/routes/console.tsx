import * as React from 'react';

import { Switch } from 'react-router';
import {
  Hero,
  InstanceSettings,
  Logos,
  NoticeBoard,
  CustomPages,
  CoursesManage
} from 'console/components';
import {
  ButtonsCustomization,
  ConsoleHome,
  Colors,
  ThemeFooterSideBar,
  ThemeNavigationPage
} from 'newConsole/components';
import { PrivateRoute } from 'auth/components';
import { ROUTES } from '../global/constants';

export const ConsoleRoutes = () => {
  return (
    <Switch>
      <PrivateRoute
        path={ROUTES.Console.INSTANCE_SETTINGS_GENERAL}
        component={InstanceSettings}
      />
      <PrivateRoute
        path={ROUTES.Console.NOTICE_BOARD}
        component={NoticeBoard}
      />
      <PrivateRoute
        path={ROUTES.Console.THEME_PREVIEW_AND_COLORS}
        component={Colors}
      />
      <PrivateRoute
        path={ROUTES.Console.THEME_BUTTONS}
        component={ButtonsCustomization}
      />
      <PrivateRoute path={ROUTES.Console.LOGOS} component={Logos} />
      <PrivateRoute
        path={ROUTES.Console.THEME_NAVIGATION}
        component={ThemeNavigationPage}
      />
      <PrivateRoute path={ROUTES.Console.HERO} component={Hero} />
      <PrivateRoute
        path={ROUTES.Console.CUSTOM_PAGES}
        component={CustomPages}
      />
      <PrivateRoute exact path={ROUTES.Console.HOME} component={ConsoleHome} />
      <PrivateRoute
        exact
        path={ROUTES.Console.THEME_FOOTER}
        component={ThemeFooterSideBar}
      />
      <PrivateRoute
        exact
        path={ROUTES.Console.COURSES}
        component={CoursesManage}
      />
    </Switch>
  );
};
