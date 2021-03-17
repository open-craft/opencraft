import * as React from 'react';
import './styles.scss';
import {
  ConsolePageCustomizationContainer,
  PreviewComponent
} from 'console/components';
import { ConsolePage, PreviewBox } from 'newConsole/components';
import { PreviewDropdown } from 'ui/components';
import { InstancesModel } from 'console/models';
import { Container, Col, Row } from 'react-bootstrap';
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
      <ConsolePage contentLoading={this.props.loading}>
        <div className="preview-header d-flex align-items-center">
          <PreviewDropdown handleChange={this.changePreview} />
          <div className="notice-container d-flex flex-row-reverse">
            <p>
              <WrappedMessage messages={messages} id="previewNotice" />
            </p>
          </div>
        </div>
        <PreviewBox>
          <ConsolePageCustomizationContainer>
            {themeData && themeData.version === 1 && (
              <Container className="preview-container">
                <Row>
                  <Col>
                    <PreviewComponent
                      instanceData={instance.data!}
                      currentPreview={this.state.currentPreview}
                    />
                  </Col>
                </Row>
              </Container>
            )}
          </ConsolePageCustomizationContainer>
        </PreviewBox>
      </ConsolePage>
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
