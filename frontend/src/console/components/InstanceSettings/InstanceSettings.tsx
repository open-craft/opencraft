import * as React from 'react';
import './styles.scss';
import {
  ConsolePage,
  ConsolePageCustomizationContainer
} from 'console/components';
import { TextInputField } from 'ui/components';
import { InstancesModel } from 'console/models';
import { connect } from 'react-redux';
import { RootState } from 'global/state';
import { WrappedMessage } from 'utils/intl';
import { updateFieldValue } from 'console/actions';
import messages from './displayMessages';

interface State {
  instanceName: string;
  publicContactEmail: string;
  // extra state to manage the empty title and subtitle and rendering
  renderBool: boolean;
}

interface ActionProps {
  updateFieldValue: Function;
}
interface StateProps extends InstancesModel {}
interface Props extends StateProps, ActionProps {}

export class InstanceSettingsComponent extends React.PureComponent<
  Props,
  State
> {
  constructor(props: Props) {
    super(props);

    this.state = {
      instanceName: '',
      publicContactEmail: '',
      renderBool: true
    };

    if (this.props.activeInstance.data) {
      this.state = {
        instanceName: this.props.activeInstance.data.instanceName,
        publicContactEmail: this.props.activeInstance.data.publicContactEmail,
        renderBool: false
      };
    }
  }

  public componentDidUpdate(prevProps: Props) {
    // Fill fields after finishing loading data
    if (this.props.activeInstance.data) {
      this.updateInitialState(this.props);
    }
    this.needToUpdateInstanceFields(prevProps);
  }

  // Set an initial state or restore empty values
  private updateInitialState = (props: Props) => {
    if (
      (this.state.instanceName.trim() === '' ||
        this.state.publicContactEmail.trim() === '') &&
      props.activeInstance.data &&
      this.state.renderBool
    ) {
      this.setState({
        instanceName: props.activeInstance.data.instanceName,
        publicContactEmail: props.activeInstance.data.publicContactEmail,
        renderBool: false
      });
    }
  };

  private needToUpdateInstanceFields = (prevProps: Props) => {
    if (
      prevProps.activeInstance.loading.includes('instanceName') &&
      !this.props.activeInstance.loading.includes('instanceName')
    ) {
      this.setState({
        instanceName: this.props.activeInstance!.data!.instanceName
      });
    }
    if (
      prevProps.activeInstance.loading.includes('publicContactEmail') &&
      !this.props.activeInstance.loading.includes('publicContactEmail')
    ) {
      this.setState({
        publicContactEmail: this.props.activeInstance!.data!.publicContactEmail
      });
    }
  };

  private onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const field = e.target.name;
    const { value } = e.target;

    this.setState({
      [field]: value
    } as Pick<State, 'instanceName' | 'publicContactEmail'>);
  };

  private updateValue = (fieldName: string, value: string) => {
    const instance = this.props.activeInstance;

    if (
      instance.data &&
      this.state[fieldName as keyof State] !== instance.data[fieldName]
    ) {
      this.props.updateFieldValue(instance.data.id, fieldName, value);
    }
  };

  public render() {
    const instance = this.props.activeInstance;

    return (
      <ConsolePage contentLoading={this.props.loading}>
        <ConsolePageCustomizationContainer>
          <h2>
            <WrappedMessage messages={messages} id="instanceSettings" />
          </h2>

          <TextInputField
            fieldName="instanceName"
            value={this.state.instanceName}
            onChange={this.onChange}
            onBlur={() => {
              this.updateValue('instanceName', this.state.instanceName);
            }}
            messages={messages}
            loading={instance.loading.includes('instanceName')}
            error={instance.feedback.instanceName}
          />

          <TextInputField
            fieldName="publicContactEmail"
            value={this.state.publicContactEmail}
            onChange={this.onChange}
            messages={messages}
            loading={instance.loading.includes('publicContactEmail')}
            onBlur={() => {
              this.updateValue(
                'publicContactEmail',
                this.state.publicContactEmail
              );
            }}
            type="email"
            error={instance.feedback.publicContactEmail}
          />
        </ConsolePageCustomizationContainer>
      </ConsolePage>
    );
  }
}

export const InstanceSettings = connect<
  StateProps,
  ActionProps,
  {},
  Props,
  RootState
>((state: RootState) => state.console, {
  updateFieldValue
})(InstanceSettingsComponent);
