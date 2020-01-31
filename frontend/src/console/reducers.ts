import update from 'immutability-helper';
import { InstancesModel, initialConsoleState } from 'console/models';
import * as Actions from './actions';

export function consoleReducer(
  state = initialConsoleState,
  action: Actions.ActionTypes
): InstancesModel {
  let keys: { [key: string]: any };
  let activeInstanceId: number;

  switch (action.type) {
    case Actions.Types.USER_INSTANCE_LIST:
      return update(state, { loading: { $set: true } });
    case Actions.Types.USER_INSTANCE_LIST_SUCCESS:
      activeInstanceId = 0;
      if (state.activeInstance.data !== null) {
        activeInstanceId = state.activeInstance.data.id;
      }

      return update(state, {
        loading: { $set: false },
        instances: { $set: action.data },
        activeInstance: {
          $merge: {
            data: action.data[activeInstanceId],
            feedback: {},
            loading: []
          }
        }
      });
    case Actions.Types.UPDATE_INSTANCE_INFO:
      return update(state, {
        activeInstance: {
          loading: {
            $push: [action.fieldName]
          }
        }
      });
    case Actions.Types.UPDATE_INSTANCE_INFO_SUCCESS:
      keys = Object.keys(action.data);

      return update(state, {
        activeInstance: {
          data: { $merge: action.data },
          loading: {
            $set: state.activeInstance.loading.filter(x => !keys.includes(x))
          }
        }
      });
    case Actions.Types.UPDATE_INSTANCE_INFO_FAILURE:
      keys = Object.keys(action.data);

      return update(state, {
        activeInstance: {
          feedback: { $merge: action.data },
          loading: {
            $set: state.activeInstance.loading.filter(x => !keys.includes(x))
          }
        }
      });
    case Actions.Types.GET_DEPLOYMENT_STATUS:
      return state;
    case Actions.Types.GET_DEPLOYMENT_STATUS_SUCCESS:
      return update(state, {
        activeInstance: {
          deployment: { $set: action.data }
        }
      });
    case Actions.Types.GET_DEPLOYMENT_STATUS_FAILURE:
      return state;
    case Actions.Types.PERFORM_DEPLOYMENT:
      return state;
    case Actions.Types.PERFORM_DEPLOYMENT_SUCCESS:
      return state;
    case Actions.Types.PERFORM_DEPLOYMENT_FAILURE:
      return state;
    default:
      return state;
  }
}
