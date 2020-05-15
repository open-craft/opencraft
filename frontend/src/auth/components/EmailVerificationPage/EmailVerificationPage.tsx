import * as React from 'react';
import { InstancesModel } from 'console/models';
import { connect } from 'react-redux';
import { RootState } from 'global/state';
import { NavLink } from 'react-router-dom';
import { ROUTES } from 'global/constants';
import { WrappedMessage } from 'utils/intl';
import { ContentPage } from 'ui/components';
import { Button, Spinner } from 'react-bootstrap';
import messages from './displayMessages';
import './styles.scss';

interface ActionProps {}
interface StateProps extends InstancesModel {}
interface Props extends StateProps, ActionProps {
  // Passing URL as parameter to custom page
  match: {
    params: {
      verificationCode: string;
    };
  };
  loading: boolean;
  error: string;
  succeeded: boolean;
}

@connect<{}, ActionProps, {}, Props, RootState>(
  (state: RootState) => state.loginState,
  {}
)
export class EmailVerificationPage extends React.PureComponent<Props> {
  componentDidMount() {
    // Make request
    console.log('asd');
  }

  public render() {
    if (this.props.loading) {
      return (
        <ContentPage title="Email Verification">
          <Spinner animation="border" role="status">
            <span className="sr-only">Loading...</span>
          </Spinner>
        </ContentPage>
      );
    }

    if (!this.props.succeeded) {
      const title = (
        <span className="page-title">
          <WrappedMessage messages={messages} id="emailVerified" />
          <i className="email-verification-title-icon far fa-check-circle fa-xs" />
        </span>
      );
      return (
        <ContentPage
          title={title}
          subtitle={<WrappedMessage messages={messages} id="thankYouMessage" />}
        >
          <div className="email-verification-container">
            <p>
              <WrappedMessage messages={messages} id="followUp" />
            </p>

            <div className="email-verification-console-button text-center">
              <NavLink exact to={ROUTES.Console.HOME}>
                <Button size="lg">
                  <WrappedMessage messages={messages} id="goToConsole" />
                  <i className="fas fa-external-link-alt fa-lg" />
                </Button>
              </NavLink>
            </div>

            <p>
              <WrappedMessage messages={messages} id="contact" />
            </p>
          </div>
        </ContentPage>
      );
    }

    return (
      <ContentPage title="Email Verification Failed">
        <p>
          <WrappedMessage messages={messages} id="failedVerification" />
        </p>
      </ContentPage>
    );
  }
}
