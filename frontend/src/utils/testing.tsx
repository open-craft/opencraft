import { createMemoryHistory } from 'history';
import * as React from 'react';
import { IntlProvider } from 'react-intl';
import { Provider } from 'react-redux';
import { MemoryRouter } from 'react-router';
import * as renderer from 'react-test-renderer';
import { createStore } from 'redux';
import { createRootReducer } from '../global/reducers';

export const setupComponentForTesting = (reactContent: JSX.Element, storeContents = {}) => {
  const store = createStore(createRootReducer(createMemoryHistory()), storeContents);
  return renderer.create(
    <IntlProvider textComponent={React.Fragment} locale="en">
      <Provider store={store}>
        <MemoryRouter>
          {reactContent}
        </MemoryRouter>
      </Provider>
    </IntlProvider>,
  );
};
