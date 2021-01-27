import * as React from 'react';
import { InstancesModel } from 'console/models';
import {
  ConsolePage,
  ConsolePageCustomizationContainer
} from 'console/components';
import { CONTACT_US_LINK, ROUTES } from 'global/constants';
import { WrappedMessage } from 'utils/intl';
import { Container, Col, Nav, Row } from 'react-bootstrap';
import { RootState } from 'global/state';
import { connect } from 'react-redux';
import messages from './displayMessages';
import './styles.scss';

interface State {
  title: string;
  subtitle: string;
  // extra state to manage the empty title and subtitle and rendering
  renderBool: boolean;
}

interface ActionProps {
  clearErrorMessage: Function;
  updateThemeFieldValue: Function;
  updateImages: Function;
}

interface StateProps extends InstancesModel {}

interface Props extends StateProps, ActionProps {}

export class CoursesManageComponent extends React.PureComponent<Props, State> {
  public render() {
    let instanceLink;
    if (this.props.activeInstance.data) {
      instanceLink = this.props.activeInstance.data.studioUrl;
    } else {
      instanceLink = ROUTES.Error.UNKNOWN_ERROR;
    }

    return (
      <ConsolePage contentLoading={this.props.loading}>
        <div className="courses-page">
          <Container fluid className="container">
            <ConsolePageCustomizationContainer>
              <Row>
                <Col md={9}>
                  <h2>
                    <WrappedMessage id="title" messages={messages} />
                  </h2>
                  <WrappedMessage id="paragraph_01" messages={messages} />
                </Col>
              </Row>
              <Row className="stepRow">
                <Col xs={1}>
                  <div className="numberCircle">
                    <p>1</p>
                  </div>
                </Col>
                <Col>
                  <WrappedMessage id="step_01" messages={messages} />
                </Col>
              </Row>
              <Row className="stepRow">
                <Col xs={1}>
                  <div className="numberCircle">
                    <p>2</p>
                  </div>
                </Col>
                <Col>
                  <WrappedMessage id="step_02" messages={messages} />
                </Col>
              </Row>
              <Row className="stepRow">
                <Col xs={1} />
                <Col>
                  <a href={instanceLink}>
                    <button
                      id="manage_button"
                      type="button"
                      className="btn btn-primary"
                    >
                      <Row>
                        <Col>
                          <p>
                            <WrappedMessage
                              id="button_text"
                              messages={messages}
                            />
                          </p>
                        </Col>
                        <Col xs={2}>
                          <i className="fas fa-external-link-alt" />
                        </Col>
                      </Row>
                    </button>
                  </a>
                </Col>
              </Row>
              <Row className="stepRow">
                <Col xs={1} />
                <Row>
                  <WrappedMessage id="help_text" messages={messages} />
                  &emsp;
                  <Nav.Link
                    className="support_link"
                    onClick={() => window.open(CONTACT_US_LINK, '_blank')}
                  >
                    <WrappedMessage id="help_link" messages={messages} />
                  </Nav.Link>
                </Row>
              </Row>
            </ConsolePageCustomizationContainer>
          </Container>
        </div>
      </ConsolePage>
    );
  }
}

export const CoursesManage = connect<
  StateProps,
  ActionProps,
  {},
  Props,
  RootState
>((state: RootState) => state.console)(CoursesManageComponent);
