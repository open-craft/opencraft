import * as React from 'react';
import { ROUTES } from 'global/constants';
import { Redirect, Route, RouteProps } from 'react-router';
import './styles.scss';

interface PrivateRouteProps extends RouteProps {
  ifUnauthorizedRedirectTo?: string;
}

export const PrivateRoute: React.FC<PrivateRouteProps> = (props: PrivateRouteProps) => {
  const fallbackRedirect = props.ifUnauthorizedRedirectTo || ROUTES.Auth.LOGOUT;
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
      <Redirect to={{ pathname: fallbackRedirect }} />
    );
    return (
      <Route path={props.path} component={renderComponent} render={undefined} />
    );
  }
  return <Route {...props} />;
};
