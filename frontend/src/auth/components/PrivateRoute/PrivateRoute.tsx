import * as React from 'react';
import { ROUTES } from 'global/constants';
import { Redirect, Route, RouteProps } from 'react-router';
import './styles.scss';

export const PrivateRoute: React.FC<RouteProps> = (props: RouteProps) => {
  const [isLoading, setIsLoading] = React.useState(true);
  const [isAuthenticated, setIsAuthenticated] = React.useState(false);

  React.useEffect(() => {
    const accessToken = localStorage.getItem('token_access');
    setIsAuthenticated(!!accessToken);
    setIsLoading(false);
  }, [setIsAuthenticated, setIsLoading]);

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
