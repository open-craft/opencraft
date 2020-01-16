import * as React from 'react';
import { connect } from 'react-redux';
import { ROUTES } from 'global/constants';
import { Redirect } from 'react-router';
import './styles.scss';
import { performLogout } from 'auth/actions';

interface ActionProps {
  performLogout: Function;
}

interface Props extends ActionProps {}

@connect<{}, ActionProps, {}, Props, {}>(() => ({}), { performLogout })
export class LogoutPage extends React.PureComponent<Props> {
  public render() {
    this.props.performLogout();

    return <Redirect to={ROUTES.Auth.LOGIN} />;
  }
}
