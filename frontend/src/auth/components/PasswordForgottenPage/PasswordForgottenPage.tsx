import * as React from 'react';
import { RootState } from 'global/state';
import { connect } from 'react-redux';
import { WrappedMessage } from 'utils/intl';
import { Alert, Button, Spinner, Form } from 'react-bootstrap';
import { ContentPage, TextInputField } from 'ui/components';
import {
  clearErrorMessage,
  clearSuccessMessage,
  performPasswordForgotten
} from 'auth/actions';
import { Link } from 'react-router-dom';
import messages from './displayMessages';
import './styles.scss';
import { ROUTES } from '../../../global/constants';

interface ActionProps {
  clearErrorMessage: Function;
  clearSuccessMessage: Function;
  performPasswordForgotten: Function;
}

interface State {
  [key: string]: string;
  email: string;
}

interface Props extends ActionProps {
  loading: boolean;
  succeeded: boolean;
  error: string;
}

@connect<{}, ActionProps, {}, Props, RootState>(
  (state: RootState) => state.loginState,
  {
    clearErrorMessage,
    clearSuccessMessage,
    performPasswordForgotten
  }
)
export class PasswordForgottenPage extends React.PureComponent<Props, State> {
  constructor(props: Props) {
    super(props);

    this.state = {
      email: ''
    };
  }

  componentDidMount(): void {
    this.props.clearErrorMessage();
    this.props.clearSuccessMessage();
  }

  componentWillUnmount(): void {
    this.props.clearErrorMessage();
    this.props.clearSuccessMessage();
  }

  private onKeyPress = (event: any) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      this.submit();
    }
  };

  private submit = () => {
    this.props.performPasswordForgotten({ email: this.state.email });
  };

  private onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const field = e.target.name;
    const { value } = e.target;

    this.setState({
      [field]: value
    });
  };

  public render() {
    return (
      <ContentPage title="Forgot password">
        <Form
          className="login" // FIXME: make SCSS more generic to properly reuse this style.
          onKeyPress={(event: any) => {
            this.onKeyPress(event);
          }}
        >
          <TextInputField
            fieldName="email"
            value={this.state.email}
            onChange={this.onChange}
            messages={messages}
            type="email"
          />

          {this.props.succeeded && (
            <Alert variant="success">
              <WrappedMessage messages={messages} id="success" />
            </Alert>
          )}

          {this.props.error && (
            <Alert variant="danger">{this.props.error}</Alert>
          )}

          <Button
            className="pull-left loading"
            variant="primary"
            size="lg"
            disabled={this.props.loading}
            onClick={() => {
              this.submit();
            }}
          >
            {this.props.loading && (
              <Spinner animation="border" size="sm" className="spinner" />
            )}
            <WrappedMessage messages={messages} id="resetPassword" />
          </Button>

          <p className="forgot-password">
            {' '}
            {/* FIXME: make SCSS more generic to properly reuse this style. */}
            <Link to={ROUTES.Auth.LOGIN}>
              <WrappedMessage messages={messages} id="signIn" />
            </Link>
          </p>
        </Form>
      </ContentPage>
    );
  }
}
