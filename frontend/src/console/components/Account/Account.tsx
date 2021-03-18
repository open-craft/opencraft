import * as React from 'react';
import { connect } from 'react-redux';
import { RootState } from 'global/state';
import { Col, Row, Form, Button, Spinner } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import { InstancesModel } from 'console/models';
import { TextInputField } from 'ui/components';
import {
  updateAccountDetails,
  getAccountDetails,
  changePassword
} from 'console/actions';
import messages from './displayMessages';
import { ConsolePage } from '../ConsolePage';
import './styles.scss';

interface ActionProps {
  updateAccountDetails: Function;
  getAccountDetails: Function;
  changePassword: Function;
}

interface State {
  [key: string]: string | boolean;
  fullName: string;
  email: string;
  oldPassword: string;
  newPassword: string;
}

interface StateProps extends InstancesModel {}

interface Props extends StateProps, ActionProps {}

export class AccountComponent extends React.PureComponent<Props, State> {
  constructor(props: Props, state: State) {
    super(props);

    const { account } = this.props;

    this.state = {
      fullName: account.fullName,
      email: account.email,
      oldPassword: '',
      newPassword: ''
    };
  }

  public componentDidMount() {
    this.props.getAccountDetails();
  }

  public componentDidUpdate(prevProps: Props, prevState: State) {
    this.updateInitialState(prevState);
  }

  private updateInitialState = (prevState: State) => {
    const { account } = this.props;

    if (account && account.fullName && !prevState.fullName) {
      this.setState({
        fullName: account.fullName,
        email: account.email,
        oldPassword: '',
        newPassword: ''
      });
    }
  };

  private onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const field = e.target.name;
    const { value } = e.target;

    this.setState({
      [field]: value
    });
  };

  private saveAccountDetails = () => {
    this.props.updateAccountDetails({
      fullName: this.state.fullName,
      email: this.state.email
    });
  };

  private saveNewPassword = () => {
    this.props.changePassword({
      oldPassword: this.state.oldPassword,
      newPassword: this.state.newPassword
    });
  };

  public render() {
    return (
      <ConsolePage
        showSidebar={false}
        contentLoading={this.props.loading}
        showToolbar={false}
      >
        <Row className="justify-content-center bg-white account-details">
          <Col md={8}>
            <div className="account-heading">
              <p>
                <WrappedMessage id="account" messages={messages} />
              </p>
            </div>
            <Form>
              <TextInputField
                fieldName="fullName"
                value={this.state.fullName}
                onChange={this.onChange}
                messages={messages}
                type="username"
                autoComplete="username"
              />
              <TextInputField
                fieldName="email"
                value={this.state.email}
                onChange={this.onChange}
                messages={messages}
                type="email"
                autoComplete="email"
              />

              <Button
                variant="primary"
                onClick={() => {
                  this.saveAccountDetails();
                }}
              >
                {this.props.accountDetailsUpdating && (
                  <Spinner animation="border" size="sm" className="spinner" />
                )}
                <WrappedMessage messages={messages} id="saveAccountDetails" />
              </Button>
            </Form>
          </Col>
        </Row>

        <Row className="justify-content-center bg-white password-change">
          <Col md={8}>
            <div className="account-heading">
              <p>
                <WrappedMessage id="updatePassword" messages={messages} />
              </p>
            </div>
            <Form>
              <TextInputField
                fieldName="oldPassword"
                value={this.state.oldPassword}
                onChange={this.onChange}
                messages={messages}
                type="password"
                autoComplete="password"
              />
              <TextInputField
                fieldName="newPassword"
                value={this.state.newPassword}
                onChange={this.onChange}
                messages={messages}
                type="password"
                autoComplete="password"
              />

              <Button
                variant="primary"
                onClick={() => {
                  this.saveNewPassword();
                }}
              >
                {this.props.passwordUpdating && (
                  <Spinner animation="border" size="sm" className="spinner" />
                )}
                <WrappedMessage messages={messages} id="saveNewPassword" />
              </Button>
            </Form>
          </Col>
        </Row>
      </ConsolePage>
    );
  }
}

export const Account = connect<{}, ActionProps, {}, Props, RootState>(
  (state: RootState) => state.console,
  {
    updateAccountDetails,
    getAccountDetails,
    changePassword
  }
)(AccountComponent);
