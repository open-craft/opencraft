import './matchMedia.mock.ts';
import { createMemoryHistory } from 'history';
import * as React from 'react';
import { IntlProvider } from 'react-intl';
import { Provider } from 'react-redux';
import { MemoryRouter } from 'react-router';
import * as renderer from 'react-test-renderer';
import { applyMiddleware, createStore } from 'redux';
import thunk from 'redux-thunk';
import { createRootReducer } from '../global/reducers';

export const setupComponentForTesting = (
  reactContent: JSX.Element,
  storeContents = {}
) => {
  const middleware = applyMiddleware(thunk);

  const store = createStore(
    createRootReducer(createMemoryHistory()),
    storeContents,
    middleware
  );

  return renderer.create(
    <IntlProvider textComponent={React.Fragment} locale="en">
      <Provider store={store}>
        <MemoryRouter>{reactContent}</MemoryRouter>
      </Provider>
    </IntlProvider>
  );
};
