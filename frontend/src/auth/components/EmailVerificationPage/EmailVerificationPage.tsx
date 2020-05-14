import * as React from 'react';
import { InstancesModel } from 'console/models';
import { connect } from 'react-redux';
import { RootState } from 'global/state';
import { WrappedMessage } from 'utils/intl';
import { ContentPage } from 'ui/components';
import { Spinner } from 'react-bootstrap';
// import { Prompt } from 'react-router';
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
          <i className="title-icon far fa-check-circle fa-xs" />
        </span>
      );
      return (
        <ContentPage title={title}>
          <div className="email-verification-container">
            <p>
              <WrappedMessage messages={messages} id="thankYouMessage" />
            </p>

            <p>
              <WrappedMessage messages={messages} id="followUp" />
            </p>

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
