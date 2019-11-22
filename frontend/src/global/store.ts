import { routerMiddleware } from 'connected-react-router';
import { History } from 'history';
import { applyMiddleware, createStore, Store } from 'redux';
import { composeWithDevTools } from 'redux-devtools-extension';
import thunk from 'redux-thunk';
import { history } from './history';
import { createRootReducer } from './reducers';
import { RootState } from './state';

function configureStore(useHistory: History, initialState?: RootState): Store<RootState> {
  let middleware = applyMiddleware(routerMiddleware(useHistory), thunk);

  if (process.env.NODE_ENV !== 'production') {
    middleware = composeWithDevTools(middleware);
  }

  return createStore(
        createRootReducer(history) as any,
        initialState as any,
        middleware,
  ) as Store<RootState>;
}

// Global redux store
export const store = configureStore(history);
