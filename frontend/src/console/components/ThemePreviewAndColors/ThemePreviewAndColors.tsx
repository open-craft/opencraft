import * as React from 'react';
import './styles.scss';
import { ConsolePage } from 'console/components';
import { ColorInputField } from 'ui/components';
import { InstancesModel } from 'console/models';
import { Container, Col, Row } from 'react-bootstrap';
import { connect } from 'react-redux';
import { RootState } from 'global/state';
import { WrappedMessage } from 'utils/intl';
import { updateThemeFieldValue } from 'console/actions';
import messages from './displayMessages';

interface State {
  [key: string]: string;
  mainColor: string;
  accentColor: string;
}

interface ActionProps {
  updateThemeFieldValue: Function;
}
interface StateProps extends InstancesModel {}
interface Props extends StateProps, ActionProps {}

export class ThemePreviewAndColorsComponent extends React.PureComponent<
  Props,
  State
> {
  constructor(props: Props) {
    super(props);

    this.state = {
      mainColor: '',
      accentColor: ''
    };
  }

  public componentDidUpdate(prevProps: Props) {
    // Fill fields after finishing loading data
    this.needToUpdateInstanceFields(prevProps);
  }

  private needToUpdateInstanceFields = (prevProps: Props) => {
    const instance = this.props.activeInstance.data;
    if (
      prevProps.activeInstance.data === null &&
      instance &&
      instance.draftThemeConfig
    ) {
      this.setState({
        mainColor: instance.draftThemeConfig.mainColor!,
        accentColor: instance.draftThemeConfig.accentColor!
      });
    }
  };

  private onChangeColor = (fieldName: string, newColor: string) => {
    const instance = this.props.activeInstance;

    if (instance.data) {
      this.props.updateThemeFieldValue(
        instance.data.id,
        fieldName,
        newColor
      );
    }
  };

  private updateValue = (fieldName: string, value: string) => {
    const instance = this.props.activeInstance;

    // Only make update request if field changed
    if (instance.data) {
      this.props.updateThemeFieldValue(
        instance.data.id,
        fieldName,
        value
      );
    }
  };

  public render() {
    const instance = this.props.activeInstance;

    return (
      <ConsolePage contentLoading={this.props.loading}>
        <h2>
          <WrappedMessage messages={messages} id="themePreviewAndColors" />
        </h2>

        <Container>
          <Row>
            <Col>
              <ColorInputField
                fieldName="mainColor"
                value={this.state.mainColor}
                onChange={this.onChangeColor}
                onBlur={() => {
                  this.updateValue('mainColor', this.state.mainColor);
                }}
                messages={messages}
                loading={instance.loading.includes('instanceName')}
              />
              <ColorInputField
                fieldName="accentColor"
                value={this.state.accentColor}
                onChange={this.onChangeColor}
                onBlur={() => {
                  this.updateValue('accentColor', this.state.accentColor);
                }}
                messages={messages}
                loading={instance.loading.includes('accentColor')}
              />
            </Col>
            <Col xs={8}>Placeholder from theme preview component</Col>
          </Row>
        </Container>
      </ConsolePage>
    );
  }
}

export const ThemePreviewAndColors = connect<
  StateProps,
  ActionProps,
  {},
  Props,
  RootState
>((state: RootState) => state.console, {
  updateThemeFieldValue
})(ThemePreviewAndColorsComponent);
