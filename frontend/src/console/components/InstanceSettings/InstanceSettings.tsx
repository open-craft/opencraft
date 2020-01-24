import * as React from 'react';
import messages from './displayMessages';
import './styles.scss';
import { ConsolePage } from 'console/components';
import { TextInputField } from 'ui/components';
import { InstancesModel } from 'console/models';
import { connect } from 'react-redux';
import { RootState } from 'global/state';


interface ActionProps {}
interface StateProps extends InstancesModel {}
interface Props extends StateProps, ActionProps {}

export class InstanceSettingsComponent extends React.PureComponent<Props> {
  public render() {
    return (
      <ConsolePage contentLoading={this.props.loading}>
        <h2>Instance settings</h2>

        <TextInputField
          fieldName="instanceName"
          value={""}
          onChange={() => {}}
          messages={messages}
          error={""}
        />

        <TextInputField
          fieldName="publicContactEmail"
          value={""}
          onChange={() => {}}
          messages={messages}
          type="email"
          error={""}
        />
      </ConsolePage>
    );
  };
};

export const InstanceSettings = connect<StateProps, ActionProps, {}, Props, RootState>(
  (state: RootState) => ({
    ...state.console
  }),
  {}
)(InstanceSettingsComponent);
