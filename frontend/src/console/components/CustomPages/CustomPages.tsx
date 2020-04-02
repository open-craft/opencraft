import * as React from 'react';
import './styles.scss';
import {
  ConsolePage,
  ConsolePageCustomizationContainer
} from 'console/components';
import { InstancesModel } from 'console/models';
import { connect } from 'react-redux';
import { RootState } from 'global/state';
import { WrappedMessage } from 'utils/intl';
import { updateFieldValue } from 'console/actions';
import RichTextEditor from 'react-rte';
import { Row, Col, Form, Button } from 'react-bootstrap';
import { Prompt } from 'react-router';
import messages from './displayMessages';

interface State {
  [key: string]: any;
  pageContent: any;
  contentChanged: boolean;
}

interface ActionProps {
  updateFieldValue: Function;
}
interface StateProps extends InstancesModel {}
interface Props extends StateProps, ActionProps {
  // Passing URL as parameter to custom page
  match: {
    params: {
      pageName: string;
    };
  };
}

export class CustomPagesComponent extends React.PureComponent<Props, State> {
  constructor(props: Props) {
    super(props);

    this.state = {
      pageContent: RichTextEditor.createEmptyValue(),
      contentChanged: false
    };
  }

  componentDidUpdate = (prevProps: Props) => {
    const previousPageName = prevProps.match.params.pageName;
    const currentPageName = this.props.match.params.pageName;

    // If the page changed, clear edit field and render the correct
    // override content.
    if (previousPageName !== currentPageName) {
      const content = RichTextEditor.createEmptyValue();

      // TODO: Add contitional once state has static fields in place to load
      // data from page

      // Since we know for sure this won't generate a infinite loop, we can
      // ignore the setState check inside componentDidUpdate for the next line
      // eslint-disable-next-line
      this.setState({
        pageContent: content,
        contentChanged: false
      });
    }
  };

  onChangeContent = (newContent: any) => {
    let hasContentChanged = false;

    console.log(newContent);
    if (this.state.pageContent !== "") {
      hasContentChanged = true;
    }

    this.setState({
      pageContent: newContent,
      contentChanged: hasContentChanged
    });
  };

  public render() {
    // const instance = this.props.activeInstance;
    const { pageName } = this.props.match.params;

    // TODO: The hide/show switch is just a placeholder component
    // We still need to add override capability to Ocim to disable
    // custom pages and hide links.

    return (
      <ConsolePage contentLoading={this.props.loading}>
        <ConsolePageCustomizationContainer>
          <div className="custom-page-editor">
            <Row>
              <Col md={8}>
                <h2>
                  <WrappedMessage messages={messages} id={pageName} />
                </h2>
              </Col>
              <Col className="page-switch-column">
                {/* This is a placeholder switch! This should be enabled when we  */}
                {/* implement the link overriding and page hiding features.  */}
                <Form className="page-switch-form">
                  <Form.Label htmlFor="show-page-switch">
                    <WrappedMessage messages={messages} id="showPage" />
                  </Form.Label>
                  <Form.Check
                    disabled
                    checked
                    type="switch"
                    label=""
                    id="show-page-switch"
                  />
                </Form>
              </Col>
            </Row>

            {/* Uncomment when the backend properly passes back LMS URL */}
            {/* <a className="pageLink" href="http://google.com">
              http://google.com
            </a> */}

            <Prompt
              when={this.state.contentChanged}
              message={messages.leavePageMessage.defaultMessage}
            />

            <div className="editor-container">
              <RichTextEditor
                value={this.state.pageContent}
                onChange={this.onChangeContent}
                className="page-editor"
                autoFocus
              />
            </div>

            <div className="page-controls">
              <Button
                className="save-custom-page"
                variant="primary"
                size="lg"
                disabled={this.props.loading || !this.state.contentChanged}
                onClick={() => {}}
              >
                <WrappedMessage messages={messages} id="save" />
              </Button>
            </div>
          </div>
        </ConsolePageCustomizationContainer>
      </ConsolePage>
    );
  }
}

export const CustomPages = connect<
  StateProps,
  ActionProps,
  {},
  Props,
  RootState
>((state: RootState) => state.console, {
  updateFieldValue
})(CustomPagesComponent);
