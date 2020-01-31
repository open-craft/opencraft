import * as React from 'react';
import './styles.scss';
import { ConsolePage } from 'console/components';
import { TextInputField } from 'ui/components';
import { InstancesModel } from 'console/models';
import { connect } from 'react-redux';
import { RootState } from 'global/state';
import { WrappedMessage } from 'utils/intl';
import { updateFieldValue } from 'console/actions';
import messages from './displayMessages';

interface State {
  [key: string]: string;
  instanceName: string;
  publicContactEmail: string;
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
      publicContactEmail: ''
    };
  }

  public componentDidUpdate(prevProps: Props) {
    // Fill fields after finishing loading data
    if (
      prevProps.activeInstance.data === null &&
      this.props.activeInstance.data
    ) {
      this.setState({
        instanceName: this.props.activeInstance.data.instanceName,
        publicContactEmail: this.props.activeInstance.data.publicContactEmail
      });
    }
  }

  private onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const field = e.target.name;
    const { value } = e.target;

    this.setState({
      [field]: value
    });
  };

  private updateValue = (fieldName: string, value: string) => {
    const instance = this.props.activeInstance;

    // Only make update request if field changed
    if (instance.data && this.state[fieldName] !== instance.data[fieldName]) {
      this.props.updateFieldValue(instance.data.id, fieldName, value);
    }
  };

  public render() {
    const instance = this.props.activeInstance;

    return (
      <ConsolePage contentLoading={this.props.loading}>
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
