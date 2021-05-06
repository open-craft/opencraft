import { InstancesModel } from 'console/models';
import * as React from 'react';
import { Button, Col, Container, Form, Modal, Row } from 'react-bootstrap';
import { RootState } from 'global/state';
import { connect } from 'react-redux';
import { TextInputField } from 'ui/components';
import { WrappedMessage } from 'utils/intl';
import { updateFieldValue, clearErrorMessage } from 'console/actions';
import { SUPPORT_LINK } from 'global/constants';
import messages from './displayMessages';
import './styles.scss';

interface State {
  showModal: boolean;
  externalDomain?: string;
  domainRightsAggrement: boolean;
  additionalFeeAggrement: boolean;
}

interface ActionProps {
  updateFieldValue: Function;
  clearErrorMessage: Function;
}

interface StateProps extends InstancesModel {}

interface Props extends StateProps, ActionProps {}

class AddDomainButtonComponent extends React.PureComponent<Props, State> {
  constructor(props: Props) {
    super(props);

    this.state = {
      showModal: false,
      externalDomain: '',
      domainRightsAggrement: false,
      additionalFeeAggrement: false
    };

    if (props.activeInstance.data) {
      this.state = {
        showModal: false,
        externalDomain: props.activeInstance.data.externalDomain,
        domainRightsAggrement: false,
        additionalFeeAggrement: false
      };
    }
  }

  public componentDidUpdate(prevProps: Props) {
    const instance = prevProps.activeInstance;
    if (!instance.data) {
      this.handleHide();
    } else if (
      prevProps.activeInstance!.data!.externalDomain !==
      this.props.activeInstance!.data!.externalDomain
    ) {
      this.handleHide();
    }
  }

  private handleShow = () => {
    this.setState({
      showModal: true
    });
  };

  private handleHide = () => {
    this.setState({
      showModal: false
    });
  };

  private handleClose = () => {
    this.setState({
      showModal: false
    });
  };

  private toggleDomainRights = () => {
    this.setState(prevState => ({
      domainRightsAggrement: !prevState.domainRightsAggrement
    }));
  };

  private toggleAdditionalFee = () => {
    this.setState(prevState => ({
      additionalFeeAggrement: !prevState.additionalFeeAggrement
    }));
  };

  private handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { value } = event.target;
    this.props.clearErrorMessage('externalDomain');
    this.setState({
      externalDomain: value
    });
  };

  private handleUpdateExternalDomain = () => {
    const instance = this.props.activeInstance;
    if (instance.data) {
      this.props.updateFieldValue(
        instance.data.id,
        'externalDomain',
        this.state.externalDomain
      );
    }
  };

  public render() {
    const instance = this.props.activeInstance;

    // Do not render if instance data is not present or if externalDomain is present
    // in instance data.
    if (!instance.data || (instance.data && instance.data.externalDomain)) {
      return null;
    }

    return (
      <div>
        <Button className="addBtn" size="lg" onClick={this.handleShow}>
          <WrappedMessage messages={messages} id="buttonText" />
        </Button>

        <Modal
          size="lg"
          show={this.state.showModal}
          onClose={this.handleClose}
          onHide={this.handleClose}
          centered
        >
          <Modal.Header className="add-domain-modal-header" closeButton />
          <Modal.Body>
            <Container className="add-domain-modal">
              <h2>
                <WrappedMessage messages={messages} id="modalTitle" />
              </h2>
              <Row>
                <Col className="add-domain-modal-description">
                  <p>
                    <span>
                      <WrappedMessage
                        messages={messages}
                        id="modalDescriptionOne"
                      />
                    </span>
                    <a
                      href="https://www.gandi.net/"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <WrappedMessage
                        messages={messages}
                        id="gandiDomainText"
                      />
                    </a>
                    <span>
                      <WrappedMessage
                        messages={messages}
                        id="modalDescriptionTwo"
                      />
                    </span>
                  </p>
                </Col>
              </Row>
              <Row>
                <Col lg={8}>
                  <TextInputField
                    value={this.state.externalDomain}
                    onChange={this.handleChange}
                    type="domain"
                    messages={messages}
                    fieldName="externalDomain"
                    autoComplete="off"
                  />
                  {instance.feedback.externalDomain ? (
                    <div className="domain-error">
                      <p className="error-msg">
                        <i className="fas fa-exclamation-triangle pr-2" />
                        <WrappedMessage
                          messages={messages}
                          id="domainErrorMessage"
                        />
                      </p>
                      <p className="error-detail">
                        <WrappedMessage
                          messages={messages}
                          id="domainErrorDescription1"
                        />
                        <a href={SUPPORT_LINK}>
                          <WrappedMessage
                            messages={messages}
                            id="contactSupport"
                          />
                        </a>
                        <WrappedMessage
                          messages={messages}
                          id="domainErrorDescription2"
                        />
                      </p>
                    </div>
                  ) : null}
                </Col>
              </Row>
              <Form.Group>
                <Form.Check type="checkbox" className="d-flex my-3">
                  <Form.Check.Input
                    type="checkbox"
                    checked={this.state.domainRightsAggrement}
                    onChange={this.toggleDomainRights}
                  />
                  <Form.Check.Label className="checkbox-label">
                    <WrappedMessage
                      messages={messages}
                      id="domainRightsAgreement"
                    />
                  </Form.Check.Label>
                </Form.Check>
                <Form.Check type="checkbox" className="d-flex my-3">
                  <Form.Check.Input
                    type="checkbox"
                    checked={this.state.additionalFeeAggrement}
                    onChange={this.toggleAdditionalFee}
                  />
                  <Form.Check.Label className="checkbox-label">
                    <WrappedMessage
                      messages={messages}
                      id="additionalFeeAgreement"
                    />
                  </Form.Check.Label>
                </Form.Check>
              </Form.Group>
              <div className="d-flex flex-row">
                <div className="verify-btn">
                  <Button
                    size="lg"
                    variant="primary"
                    disabled={
                      !(
                        this.state.additionalFeeAggrement &&
                        this.state.domainRightsAggrement &&
                        !!this.state.externalDomain
                      )
                    }
                    onClick={this.handleUpdateExternalDomain}
                  >
                    <WrappedMessage messages={messages} id="addDomainBtn" />
                  </Button>
                </div>
                <div>
                  <Button
                    size="lg"
                    variant="outline-primary"
                    onClick={this.handleHide}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            </Container>
          </Modal.Body>
        </Modal>
      </div>
    );
  }
}

export const AddDomainButton = connect<
  StateProps,
  ActionProps,
  {},
  Props,
  RootState
>((state: RootState) => state.console, {
  updateFieldValue,
  clearErrorMessage
})(AddDomainButtonComponent);
