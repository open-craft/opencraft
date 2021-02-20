import * as React from 'react';
import { InstancesModel } from 'console/models';
import { ConsolePage } from 'newConsole/components';
import { CONTACT_US_LINK } from 'global/constants';
import { WrappedMessage } from 'utils/intl';
import { Col, Button, Row } from 'react-bootstrap';
import { RootState } from 'global/state';
import { connect } from 'react-redux';
import messages from './displayMessages';
import './styles.scss';
import { PreviewBox } from '../PreviewBox';

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
      instanceLink = '';
    }

    return (
      <ConsolePage contentLoading={this.props.loading}>
        <PreviewBox>
          <div className="courses-page">
            <div>
              <h2>
                <WrappedMessage id="title" messages={messages} />
              </h2>
              <WrappedMessage id="explanation" messages={messages} />
              <div className="list-items">
                <Row>
                  <Col xs={1}>
                    <div className="number-circle">
                      <p>1</p>
                    </div>
                  </Col>
                  <Col>
                    <WrappedMessage
                      id="instructions_access"
                      messages={messages}
                    />
                  </Col>
                </Row>
                <Row>
                  <Col xs={1}>
                    <div className="number-circle">
                      <p>2</p>
                    </div>
                  </Col>
                  <Col>
                    <WrappedMessage
                      id="instructions_credentials"
                      messages={messages}
                    />
                  </Col>
                </Row>
              </div>

              <p>
                <a href={instanceLink}>
                  <Button
                    className="manageBtn"
                    disabled={instanceLink === ''}
                    size="lg"
                  >
                    <WrappedMessage messages={messages} id="button_text" />
                    <i className="fas fa-external-link-alt fa-m" />
                  </Button>
                </a>
              </p>

              <h6>
                <WrappedMessage id="help_text" messages={messages} />
                <a
                  className="support-link"
                  href={CONTACT_US_LINK}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <WrappedMessage id="help_link" messages={messages} />
                </a>
              </h6>
            </div>
          </div>
        </PreviewBox>
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
