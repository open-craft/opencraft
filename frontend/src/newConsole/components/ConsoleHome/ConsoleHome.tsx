import * as React from 'react';
import {
  ConsolePage,
  PreviewBox,
  CourseOutlinePreview
} from 'newConsole/components';
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

export class ConsoleHomeComponent extends React.PureComponent<Props, State> {
  public render() {
    return (
      <ConsolePage
        contentLoading={this.props.loading}
        showSideBarEditComponent={false}
      >
        <PreviewBox>
          <CourseOutlinePreview />
        </PreviewBox>
      </ConsolePage>
    );
  }
}

export const ConsoleHome = connect<
  StateProps,
  ActionProps,
  {},
  Props,
  RootState
>((state: RootState) => state.console)(ConsoleHomeComponent);
