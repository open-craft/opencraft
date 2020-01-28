import update from 'immutability-helper';
import { InstancesModel, initialConsoleState } from 'console/models';
import * as Actions from './actions';

export function consoleReducer(
  state = initialConsoleState,
  action: Actions.ActionTypes
): InstancesModel {
  switch (action.type) {
    case Actions.Types.USER_INSTANCE_LIST:
      return update(state, { loading: { $set: true } });
    case Actions.Types.USER_INSTANCE_LIST_SUCCESS:
      return update(state, {
        loading: { $set: false },
        instances: { $set: action.data },
        selectedInstance: { $set: 0 }
      });
    default:
      return state;
  }
}
