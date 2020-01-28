import * as React from 'react';
import './styles.scss';
import { ConsolePage } from 'console/components';
import { TextInputField } from 'ui/components';
import { InstancesModel } from 'console/models';
import { connect } from 'react-redux';
import { RootState } from 'global/state';
import { WrappedMessage } from 'utils/intl';
import messages from './displayMessages';

interface State {
  [key: string]: string;
  instanceName: string;
  publicContactEmail: string;
}

interface ActionProps {}
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

  private onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const field = e.target.name;
    const { value } = e.target;

    this.setState({
      [field]: value
    });
  };

  public render() {
    return (
      <ConsolePage contentLoading={this.props.loading}>
        <h2>
          <WrappedMessage messages={messages} id="instanceSettings" />
        </h2>

        <TextInputField
          fieldName="instanceName"
          value={this.state.instanceName}
          onChange={this.onChange}
          messages={messages}
          error=""
        />

        <TextInputField
          fieldName="publicContactEmail"
          value={this.state.publicContactEmail}
          onChange={this.onChange}
          messages={messages}
          type="email"
          error=""
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
>(
  (state: RootState) => state.console,
  {}
)(InstanceSettingsComponent);
