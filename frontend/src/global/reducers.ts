import { connectRouter } from 'connected-react-router';
import { History } from 'history';
import { combineReducers } from 'redux';
import { registrationReducer } from '../registration/reducers';
import { loginStateReducer } from '../auth/reducers';
import { consoleReducer } from '../console/reducers';
import { uiStateReducer } from '../ui/reducers';

export const createRootReducer = (history: History) =>
  combineReducers({
    console: consoleReducer,
    loginState: loginStateReducer,
    registration: registrationReducer,
    router: connectRouter(history),
    ui: uiStateReducer
  });
