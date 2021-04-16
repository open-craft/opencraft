import * as React from 'react';
import './styles.scss';
import { PreviewComponent } from 'console/components';
import { PreviewBox } from 'newConsole/components';
import { PreviewDropdown } from 'ui/components';
import { InstancesModel } from 'console/models';
import { Col, Row } from 'react-bootstrap';
import { connect } from 'react-redux';
import { RootState } from 'global/state';
import { WrappedMessage } from 'utils/intl';
import { updateThemeFieldValue } from 'console/actions';
import messages from './displayMessages';

interface State {
  currentPreview: string;
}
interface ActionProps {
  updateThemeFieldValue: Function;
}
interface StateProps extends InstancesModel {}
interface Props extends StateProps, ActionProps {}

export class ThemePreviewComponent extends React.PureComponent<Props, State> {
  constructor(props: Props, state: State) {
    super(props);
    this.state = {
      currentPreview: 'dashboard'
    };
  }

  private changePreview = (page: string) => {
    this.setState({
      currentPreview: page
    });
  };

  public render() {
    const instance = this.props.activeInstance;
    let themeData;

    if (instance.data && instance.data.draftThemeConfig) {
      themeData = instance.data.draftThemeConfig;
    }

    return (
      <Row className="m-0">
        <Col md="4" className="p-0">
          <div className="preview-header d-flex justify-content-start">
            <PreviewDropdown handleChange={this.changePreview} />
          </div>
        </Col>
        <Col md="8" className="p-0 align-items-start">
          <div className="notice-container d-flex justify-content-end">
            <WrappedMessage messages={messages} id="previewNotice" />
          </div>
        </Col>
        <PreviewBox>
          {themeData && themeData.version === 1 && (
            <PreviewComponent
              instanceData={instance.data!}
              currentPreview={this.state.currentPreview}
            />
          )}
        </PreviewBox>
      </Row>
    );
  }
}

export const ThemePreview = connect<
  StateProps,
  ActionProps,
  {},
  Props,
  RootState
>((state: RootState) => state.console, {
  updateThemeFieldValue
})(ThemePreviewComponent);
