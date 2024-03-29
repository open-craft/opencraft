import 'utils/setup_tinymce';
import * as React from 'react';
import './styles.scss';
import {
  ConsolePage,
  ConsolePageCustomizationContainer
} from 'newConsole/components';
import { LMS_CUSTOM_PAGE_LINK_MAP } from 'global/constants';
import { InstancesModel } from 'console/models';
import { connect } from 'react-redux';
import { RootState } from 'global/state';
import { WrappedMessage } from 'utils/intl';
import {
  updateStaticContentOverridesFieldValue,
  toggleStaticPageVisibility
} from 'console/actions';
import { capitalizeFirstLetter } from 'utils/string_utils';
import { StaticContentOverrides } from 'ocim-client';
import { Row, Col, Form } from 'react-bootstrap';
import { Prompt } from 'react-router';
import { Editor } from '@tinymce/tinymce-react';
import messages from './displayMessages';

interface State {
  [key: string]: any;
  pageContent: any;
}
interface ActionProps {
  updateStaticContentOverridesFieldValue: Function;
  toggleStaticPageVisibility: Function;
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
      pageContent: this.getPageContentFromState(),
      enabled: true
    };
  }

  componentDidUpdate = (prevProps: Props) => {
    const previousPageName = prevProps.match.params.pageName;
    const currentPageName = this.props.match.params.pageName;

    // If the page changed, clear edit field and render the correct
    // override content.
    if (previousPageName !== currentPageName) {
      // Since we know for sure this won't generate a infinite loop, we can
      // ignore the setState check inside componentDidUpdate for the next line
      // eslint-disable-next-line
      this.setState({
        pageContent: this.getPageContentFromState(),
        enabled: this.getPageVisibilitiyStatus()
      });
    }

    // If page is receiving new instance data check and update internal state
    // This prevents the internal state to be "" (empty) if data isn't available
    // when the component is created but is available later.
    if (
      prevProps.activeInstance.data == null &&
      this.props.activeInstance.data
    ) {
      // eslint-disable-next-line
      this.setState({
        pageContent: this.getPageContentFromState(),
        enabled: this.getPageVisibilitiyStatus()
      });
    }
  };

  getApiPageName = () => {
    const pageName = capitalizeFirstLetter(this.props.match.params.pageName);
    return `staticTemplate${pageName}Content` as keyof StaticContentOverrides;
  };

  getPageVisibilitiyStatus = () => {
    const { pageName } = this.props.match.params;
    let enabled = true;
    const { data } = this.props.activeInstance;
    if (data && data.staticPagesEnabled) {
      enabled = data?.staticPagesEnabled[pageName];
    }
    return enabled;
  };

  getPageContentFromState = () => {
    let content = '';
    const instance = this.props.activeInstance;

    if (
      instance &&
      instance.data &&
      instance.data.draftStaticContentOverrides
    ) {
      const statePageContent =
        instance.data.draftStaticContentOverrides[this.getApiPageName()];
      if (typeof statePageContent === 'string') {
        content = statePageContent;
      }
    }

    return content;
  };

  hasContentChanged = () => {
    return this.state.pageContent !== this.getPageContentFromState();
  };

  onChangeContent = (newContent: any) => {
    this.setState({
      pageContent: newContent
    });
  };

  getLMSLinkForPage = () => {
    const instance = this.props.activeInstance;
    const { pageName } = this.props.match.params;

    if (instance && instance.data && instance.data.lmsUrl) {
      const link = `${instance.data.lmsUrl}${LMS_CUSTOM_PAGE_LINK_MAP[pageName]}`;
      return (
        <a className="pageLink" href={link}>
          {link}
        </a>
      );
    }

    return <></>;
  };

  saveChanges = () => {
    if (this.hasContentChanged()) {
      this.props.updateStaticContentOverridesFieldValue(
        this.props.activeInstance.data!.id,
        this.getApiPageName(),
        this.state.pageContent
      );
    }
  };

  onChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const pageName = e.target.name;
    const enabled = e.target.checked;
    this.setState({ enabled });
    try {
      await this.props.toggleStaticPageVisibility(
        this.props.activeInstance.data!.id,
        pageName,
        enabled
      );
    } catch (error) {
      this.setState({ enabled: !enabled });
    }
  };

  public render() {
    const instance = this.props.activeInstance;
    const { pageName } = this.props.match.params;

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
                <Form className="page-switch-form">
                  <Form.Label htmlFor="show-page-switch">
                    <WrappedMessage messages={messages} id="showPage" />
                  </Form.Label>
                  <Form.Check
                    label=""
                    type="switch"
                    name={pageName}
                    checked={this.state.enabled}
                    id="show-page-switch"
                    onChange={this.onChange}
                  />
                </Form>
              </Col>
            </Row>

            {/* Construct LMS link and render on page */}
            {this.getLMSLinkForPage()}

            <Prompt
              when={this.hasContentChanged()}
              message={messages.leavePageMessage.defaultMessage}
            />

            <div className="editor-container">
              <Editor
                value={this.getPageContentFromState()}
                init={{
                  height: 500,
                  menubar: false,
                  plugins: [
                    'advlist autolink lists link image charmap print preview anchor',
                    'searchreplace visualblocks code fullscreen',
                    'insertdatetime media table paste code help wordcount'
                  ],
                  toolbar:
                    'bold italic backcolor | formatselect | ' +
                    'alignleft aligncenter alignright alignjustify | ' +
                    'bullist numlist | image | removeformat | undo redo'
                }}
                onEditorChange={this.onChangeContent}
                onBlur={this.saveChanges}
                disabled={instance.loading.includes(
                  'draftStaticContentOverrides'
                )}
              />
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
  updateStaticContentOverridesFieldValue,
  toggleStaticPageVisibility
})(CustomPagesComponent);
