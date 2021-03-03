import * as React from 'react';
import './styles.scss';
import { InstancesModel } from 'console/models';
import { connect } from 'react-redux';
import { updateThemeFieldValue } from 'console/actions';
import { RootState } from 'global/state';
import { Col, Container, Row } from 'react-bootstrap';
import { ColorInputField } from 'ui/components';
import messages from './displayMessages';

interface State {}
interface ActionProps {
  updateThemeFieldValue: Function;
}
interface StateProps extends InstancesModel {}
interface Props extends StateProps, ActionProps {}

class ThemeColorsComponent extends React.PureComponent<Props, State> {
  private onChangeColor = (fieldName: string, newColor: string) => {
    const instance = this.props.activeInstance;

    if (instance.data) {
      this.props.updateThemeFieldValue(instance.data.id, fieldName, newColor);
    }
  };

  public render() {
    const instance = this.props.activeInstance;
    let themeData;

    if (instance.data && instance.data.draftThemeConfig) {
      themeData = instance.data.draftThemeConfig;
    }

    if (themeData && themeData.version === 1) {
      return (
        <Row>
          <Col className="side-buttons">
            <ColorInputField
              fieldName="mainColor"
              initialValue={themeData.mainColor}
              onChange={this.onChangeColor}
              messages={messages}
              loading={instance.loading.includes('draftThemeConfig')}
            />
            <ColorInputField
              fieldName="linkColor"
              initialValue={themeData.linkColor}
              onChange={this.onChangeColor}
              messages={messages}
              loading={instance.loading.includes('draftThemeConfig')}
            />
          </Col>
        </Row>
      );
    }
    return <Container />;
  }
}

export const ThemeColors = connect<
  StateProps,
  ActionProps,
  {},
  Props,
  RootState
>((state: RootState) => state.console, {
  updateThemeFieldValue
})(ThemeColorsComponent);
