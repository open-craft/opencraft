import * as React from 'react';
import { RedeploymentToolbar, ThemePreview } from 'console/components';
import { CustomizationSideMenu } from 'newConsole/components';
import { EmailActivationAlertMessage, ErrorPage } from 'ui/components';
import { OCIM_API_BASE, ROUTES } from 'global/constants';
import { Link } from 'react-router-dom';
import { Row, Col, Container, Nav, NavItem } from 'react-bootstrap';
import { InstancesModel } from 'console/models';
import { RootState } from 'global/state';
import { connect } from 'react-redux';
import {
  listUserInstances,
  getDeploymentStatus,
  performDeployment,
  cancelDeployment
} from 'console/actions';
import { WrappedMessage } from 'utils/intl';
import messages from 'console/components/ConsolePage/displayMessages';
import './styles.scss';

interface ActionProps {
  cancelDeployment: Function;
  getDeploymentStatus: Function;
  listUserInstances: Function;
  performDeployment: Function;
}

interface StateProps extends InstancesModel {}
interface Props extends StateProps, ActionProps {
  children: React.ReactNode;
  contentLoading: boolean;
  showSidebar: boolean;
  showSideBarEditComponent: boolean;
}

interface CustomizationContainerProps {
  children: React.ReactNode;
}

export const ConsolePageCustomizationContainer: React.FC<CustomizationContainerProps> = (
  props: CustomizationContainerProps
) => <div className="customization-form">{props.children}</div>;

export class ConsolePageComponent extends React.PureComponent<Props> {
  refreshInterval?: NodeJS.Timer;

  // eslint-disable-next-line react/static-property-placement
  public static defaultProps: Partial<Props> = {
    showSidebar: true
  };

  public componentDidMount() {
    if (!this.props.loading && this.props.activeInstance.data === null) {
      this.props.listUserInstances();
    }

    this.refreshInterval = setInterval(() => {
      if (this.props.activeInstance.data) {
        this.props.getDeploymentStatus(this.props.activeInstance.data.id);
      }
    }, 5000);
  }

  componentWillUnmount() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
  }

  private performDeployment() {
    if (this.props.activeInstance.data) {
      this.props.performDeployment(this.props.activeInstance.data.id);
    }
  }

  private cancelDeployment() {
    if (this.props.activeInstance.data) {
      this.props.cancelDeployment(this.props.activeInstance.data.id);
    }
  }

  public render() {
    const renderBackButton = () => {
      return (
        <Nav className="ml-auto">
          <NavItem>
            <Link className="nav-link px-0" to={ROUTES.Console.HOME}>
              <span>
                <i className="fa fa-angle-left sm" aria-hidden="true" />
              </span>
              <span className="back-button">
                <WrappedMessage messages={messages} id="back" />
              </span>
            </Link>
          </NavItem>
        </Nav>
      );
    };

    const content = () => {
      let innerContent = this.props.children;

      if (this.props.contentLoading) {
        innerContent = (
          <ConsolePageCustomizationContainer>
            <div className="loading">
              <i className="fas fa-2x fa-sync-alt fa-spin" />
            </div>
          </ConsolePageCustomizationContainer>
        );
      }

      if (this.props.showSidebar && !this.props.showSideBarEditComponent) {
        innerContent = (
          <Row className="justify-content-center m-0">
            <Col md="3" className="p-0 m-0">
              <CustomizationSideMenu />
            </Col>
            <Col md="9" className="pr-0">
              {innerContent}
            </Col>
          </Row>
        );
      }

      if (this.props.showSidebar && this.props.showSideBarEditComponent) {
        innerContent = (
          <Row className="justify-content-center m-0">
            <Col md="3" className="p-0 m-0 pl-4">
              {renderBackButton()}
              {innerContent}
            </Col>
            {!this.props.contentLoading && (
              <Col md="9" className="pr-0">
                <ThemePreview />
              </Col>
            )}
          </Row>
        );
      }

      return innerContent;
    };
    if (
      this.props.error &&
      this.props.error.code === 'NOT_ACCESSIBLE_TO_STAFF'
    ) {
      return (
        <ErrorPage
          messages={messages}
          messageId="notAllowedForStaff"
          values={{
            link: (text: string) => (
              <a href={`${OCIM_API_BASE}/instance`}>{text}</a>
            )
          }}
        />
      );
    }

    let deploymentLoading = true;
    if (this.props.activeInstance && this.props.activeInstance.loading) {
      deploymentLoading = this.props.activeInstance.loading.includes(
        'deployment'
      );
    }

    let isEmailVerified = true;
    if (this.props.activeInstance && this.props.activeInstance.data) {
      isEmailVerified = this.props.activeInstance.data.isEmailVerified;
    }

    return (
      <div className="console-page">
        {!isEmailVerified ? (
          <EmailActivationAlertMessage />
        ) : (
          <RedeploymentToolbar
            deployment={
              this.props.activeInstance
                ? this.props.activeInstance.deployment
                : undefined
            }
            cancelRedeployment={() => {
              this.cancelDeployment();
            }}
            performDeployment={() => {
              this.performDeployment();
            }}
            loading={deploymentLoading}
          />
        )}

        <div className="new-console-page-container">
          <Row className="new-console-page-content">
            <Container fluid className="pr-4 pl-0">
              {content()}
            </Container>
          </Row>
        </div>
      </div>
    );
  }
}

export const ConsolePage = connect<
  StateProps,
  ActionProps,
  {},
  Props,
  RootState
>((state: RootState) => state.console, {
  cancelDeployment,
  getDeploymentStatus,
  listUserInstances,
  performDeployment
})(ConsolePageComponent);
