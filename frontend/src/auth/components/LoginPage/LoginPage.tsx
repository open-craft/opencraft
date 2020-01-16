import * as React from 'react';
import { RootState } from 'global/state';
import messages from './displayMessages';
import { connect } from 'react-redux';
import { ROUTES } from 'global/constants';
import { WrappedMessage } from 'utils/intl';
import { Alert, Button, Spinner, Form } from 'react-bootstrap';
import { ContentPage, TextInputField } from 'ui/components';
import { performLogin } from 'auth/actions';
import './styles.scss';

interface ActionProps {
  performLogin: Function;
}

interface State {
  [key: string]: string | boolean;
  username: string;
  password: string;
}

interface Props extends ActionProps {
  loading: boolean;
  error: string;
}

@connect<{}, ActionProps, {}, Props, RootState>(
  (state: RootState) => ({
    ...state.loginState
  }),
  {
    performLogin
  }
)
export class LoginPage extends React.PureComponent<Props, State> {
  constructor(props: Props, state: State) {
    super(props);

    this.state = {
      username: state.username,
      password: ''
    };
  }

  private logIn = () => {
    this.props.performLogin(
      {
        username: this.state.username,
        password: this.state.password
      },
      ROUTES.Console.HOME
    );
  };

  private onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const field = e.target.name;
    let value = e.target.value;

    this.setState({
      [field]: value
    });
  };

  public render() {
    return (
      <ContentPage
        title="Log in to customize your instance"
      >
        <Form className="login">
          <TextInputField
            fieldName="username"
            value={this.state.username}
            onChange={this.onChange}
            messages={messages}
            type="username"
          />
          <TextInputField
            fieldName="password"
            value={this.state.password}
            onChange={this.onChange}
            messages={messages}
            type="password"
          />

          {this.props.error && (
            <Alert variant="danger">
              {this.props.error}
            </Alert>
          )}


          <Button
            className="pull-left loading"
            variant="primary"
            size="lg"
            disabled={this.props.loading}
            onClick={() => {
              this.logIn();
            }}
          >
            {this.props.loading && (
              <Spinner animation="border" size="sm" className="spinner" />
            )}
            <WrappedMessage messages={messages} id="login" />
          </Button>

          <p className="forgot-password">
            <a href="/#">
              <WrappedMessage messages={messages} id="forgotPassword" />
            </a>
          </p>

        </Form>

      </ContentPage>
    );
  };
};
