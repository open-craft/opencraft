import * as React from 'react';
import './styles.scss';
import { ConsolePage, PreviewBox } from 'newConsole/components';
import { InstancesModel } from 'console/models';
import { connect } from 'react-redux';
import { RootState } from 'global/state';

interface State {}
interface ActionProps {
  clearErrorMessage: Function;
  updateImages: Function;
}
interface StateProps extends InstancesModel {}
interface Props extends StateProps, ActionProps {}

export class LogosComponent extends React.PureComponent<Props, State> {
  public render() {
    return (
      <ConsolePage contentLoading={this.props.loading}>
        <PreviewBox />
      </ConsolePage>
    );
  }
}

export const Logos = connect<StateProps, ActionProps, {}, Props, RootState>(
  (state: RootState) => state.console
)(LogosComponent);
