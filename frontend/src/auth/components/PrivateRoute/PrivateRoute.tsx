import * as React from 'react';
import { ROUTES } from 'global/constants';
import { Redirect, Route, RouteProps } from 'react-router';
import './styles.scss';
import { checkAuthAndRefreshToken } from 'auth/utils/helpers';

export const PrivateRoute: React.FC<RouteProps> = (props: RouteProps) => {
  const [isLoading, setIsLoading] = React.useState(true);
  const [isAuthenticated, setIsAuthenticated] = React.useState(false);

  React.useEffect(() => {
    checkAuthAndRefreshToken().then((authenticated: boolean) => {
      setIsAuthenticated(authenticated);
      setIsLoading(false);
    });
  });

  if (isLoading) {
    return null;
  }

  if (!isAuthenticated) {
    const renderComponent = () => (
      <Redirect to={{ pathname: ROUTES.Auth.LOGOUT }} />
    );
    return (
      <Route path={props.path} component={renderComponent} render={undefined} />
    );
  }
  return <Route path={props.path} component={props.component} />;
};
