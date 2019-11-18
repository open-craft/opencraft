import * as React from 'react';

import { Route, Switch } from "react-router";
import { ROUTES } from "../global/constants";
import { RegistrationContainer } from "../registration/components";
import { Home } from "../ui/components/Home";

export const MainRoutes = () => (
    <Switch>
        <Route exact path="/" component={Home}/>
        <Route path={ROUTES.Registration.HOME} component={RegistrationContainer}/>
    </Switch>
);
