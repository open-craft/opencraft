import * as Actions from './actions';
import { InstanceModel, initialConsoleState } from './models';

// Placeholder until redeployment endpoints are implemented
export function consoleReducer(
  state = initialConsoleState,
  action: Actions.ActionTypes
): InstanceModel {
  switch (action.type) {
    default:
      return state;
  }
}
