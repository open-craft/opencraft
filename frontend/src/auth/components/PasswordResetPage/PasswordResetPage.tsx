import * as React from 'react';
import { RootState } from 'global/state';
import { connect } from 'react-redux';
import { WrappedMessage } from 'utils/intl';
import { Alert, Button, Spinner, Form } from 'react-bootstrap';
import { ContentPage, TextInputField } from 'ui/components';
import {
  clearErrorMessage,
  performPasswordReset,
  performPasswordResetTokenValidation
} from 'auth/actions';
import messages from './displayMessages';
import './styles.scss';

interface ActionProps {
  clearErrorMessage: Function;
  performPasswordResetTokenValidation: Function;
  performPasswordReset: Function;
}

interface State {
  [key: string]: string;
  password: string;
  passwordConfirm: string;
}

interface Props extends ActionProps {
  // Retrieve token from URL
  match: {
    params: {
      token: string;
    };
  };
  loading: boolean;
  error: string;
  succeeded: boolean;
}

@connect<{}, ActionProps, {}, Props, RootState>(
  (state: RootState) => state.loginState,
  {
    clearErrorMessage,
    performPasswordResetTokenValidation,
    performPasswordReset
  }
)
export class PasswordResetPage extends React.PureComponent<Props, State> {
  constructor(props: Props, state: State) {
    super(props);

    this.state = {
      password: '',
      passwordConfirm: ''
    };

    this.props.performPasswordResetTokenValidation({
      token: this.props.match.params.token
    });
  }

  private validatePasswords = () => {
    return (
      this.state.password && this.state.password === this.state.passwordConfirm
    );
  };

  private onKeyPress = (event: any) => {
    if (event.key === 'Enter' && this.validatePasswords()) {
      event.preventDefault();
      this.submit();
    }
  };

  private submit = () => {
    this.props.performPasswordReset({
      token: this.props.match.params.token,
      password: this.state.password
    });
  };

  private onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const field = e.target.name;
    const { value } = e.target;

    // Clear error message when user changes a field
    this.setState({
      [field]: value
    });

    this.props.clearErrorMessage();
  };

  public render() {
    return (
      <ContentPage title="Reset your password">
        {!this.props.succeeded &&
          (!this.props.error ? (
            <div>
              <Spinner animation="border" size="sm" className="spinner" />
              <WrappedMessage messages={messages} id="validatingToken" />
            </div>
          ) : (
            <WrappedMessage messages={messages} id="invalidToken" />
          ))}

        {this.props.succeeded && (
          <Form
            className="login" // FIXME: make SCSS more generic to properly reuse this style.
            onKeyPress={(event: any) => {
              this.onKeyPress(event);
            }}
          >
            <TextInputField
              fieldName="password"
              value={this.state.password}
              onChange={this.onChange}
              type="password"
              messages={messages}
            />
            <TextInputField
              fieldName="passwordConfirm"
              value={this.state.passwordConfirm}
              onChange={this.onChange}
              type="password"
              messages={messages}
            />

            {this.props.error && (
              <Alert variant="danger">{this.props.error}</Alert>
            )}

            {this.state.password !== this.state.passwordConfirm && (
              <Alert variant="danger">
                <WrappedMessage messages={messages} id="passwordsDoNotMatch" />
              </Alert>
            )}

            <Button
              className="pull-left loading"
              variant="primary"
              size="lg"
              disabled={this.props.loading || !this.validatePasswords()}
              onClick={() => {
                this.submit();
              }}
            >
              {this.props.loading && (
                <Spinner animation="border" size="sm" className="spinner" />
              )}
              <WrappedMessage messages={messages} id="reset" />
            </Button>
          </Form>
        )}
      </ContentPage>
    );
  }
}
