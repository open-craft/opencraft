import * as React from 'react';
import { RootState } from 'global/state';
import { connect } from 'react-redux';
import { ROUTES } from 'global/constants';
import { Redirect } from 'react-router';
import './styles.scss';
import { performLogout } from 'auth/actions';
import './styles.scss';

interface ActionProps {
  performLogout: Function;
}

interface Props extends ActionProps {}

@connect<{}, ActionProps, {}, Props, RootState>(
  (state: RootState) => ({
    ...state.loginState
  }),
  {
    performLogout
  }
)
export class LogoutPage extends React.PureComponent<Props> {
  public render() {
    this.props.performLogout();

    return <Redirect to={ROUTES.Auth.LOGIN} />
  }
};
