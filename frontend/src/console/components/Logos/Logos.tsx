import * as React from 'react';
import './styles.scss';
import {
  ConsolePage,
  ConsolePageCustomizationContainer
} from 'console/components';
import { Row, Col } from 'react-bootstrap';
import { InstancesModel } from 'console/models';
import { connect } from 'react-redux';
import { RootState } from 'global/state';
import { WrappedMessage } from 'utils/intl';
import { updateThemeFieldValue } from 'console/actions';
import messages from './displayMessages';

interface State {}
interface ActionProps {
  updateThemeFieldValue: Function;
}
interface StateProps extends InstancesModel {}
interface Props extends StateProps, ActionProps {}

export class LogosComponent extends React.PureComponent<Props, State> {
  public render() {
    const instance = this.props.activeInstance;
    let themeData;
    console.log(themeData);

    if (instance.data && instance.data.draftThemeConfig) {
      themeData = instance.data.draftThemeConfig;
    }

    return (
      <div className="custom-logo-pages">
        <ConsolePage contentLoading={this.props.loading}>
          <ConsolePageCustomizationContainer>
            <Row>
              <Col md={9}>
                <h2>
                  <WrappedMessage messages={messages} id="logo" />
                </h2>
                <p>
                  <WrappedMessage messages={messages} id="logoDescription" />
                </p>
              </Col>
              <Col md={3}>
                <img src="" alt="Logo" />
              </Col>
            </Row>
          </ConsolePageCustomizationContainer>
          <ConsolePageCustomizationContainer>
            <Row>
              <Col md={9}>
                <h2>
                  <WrappedMessage messages={messages} id="favicon" />
                </h2>
                <p>
                  <WrappedMessage messages={messages} id="faviconDescription" />
                </p>
              </Col>
              <Col md={3}>
                <img src="" alt="Logo" />
              </Col>
            </Row>
          </ConsolePageCustomizationContainer>
        </ConsolePage>
      </div>
    );
  }
}

export const Logos = connect<StateProps, ActionProps, {}, Props, RootState>(
  (state: RootState) => state.console,
  {
    updateThemeFieldValue
  }
)(LogosComponent);
