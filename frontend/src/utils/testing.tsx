import { createMemoryHistory } from 'history';
import * as React from 'react';
import { IntlProvider } from 'react-intl';
import { Provider } from 'react-redux';
import { MemoryRouter } from 'react-router';
import * as renderer from 'react-test-renderer';
import { applyMiddleware, createStore } from 'redux';
import thunk from 'redux-thunk';
import { shallow, configure, render, mount } from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
import { createRootReducer } from '../global/reducers';

configure({ adapter: new Adapter() });

/*
  setupComponentForTesting:
  Renders a component tree for the passed JSX Element
  This method doesn't support UI simulations.
  Used for testing snapshots, mostly.
*/
export const setupComponentForTesting = (
  reactContent: JSX.Element,
  storeContents = {},
  dispatchMock?: (...args: any[]) => any
) => {
  const middleware = applyMiddleware(thunk);

  const store = createStore(
    createRootReducer(createMemoryHistory()),
    storeContents,
    middleware
  );

  if (dispatchMock) {
    store.dispatch = dispatchMock;
  }

  return renderer.create(
    <IntlProvider textComponent={React.Fragment} locale="en">
      <Provider store={store}>
        <MemoryRouter>{reactContent}</MemoryRouter>
      </Provider>
    </IntlProvider>
  );
};

/*
  shallowComponentForTesting:
  Renders a childless component for the passed JSX Element
*/
export const shallowComponentForTesting = (
  reactContent: JSX.Element,
  storeContents = {},
  dispatchMock?: (...args: any[]) => any
) => {
  const middleware = applyMiddleware(thunk);

  const store = createStore(
    createRootReducer(createMemoryHistory()),
    storeContents,
    middleware
  );

  if (dispatchMock) {
    store.dispatch = dispatchMock;
  }

  return shallow(
    <IntlProvider textComponent={React.Fragment} locale="en">
      <Provider store={store}>
        <MemoryRouter>{reactContent}</MemoryRouter>
      </Provider>
    </IntlProvider>
  );
};

/*
  renderComponentForTesting:
  Renders a component tree for the passed JSX Element
  Doesn't apply lifecycle methods on the children.
*/
export const renderComponentForTesting = (
  reactContent: JSX.Element,
  storeContents = {},
  dispatchMock?: (...args: any[]) => any
) => {
  const middleware = applyMiddleware(thunk);

  const store = createStore(
    createRootReducer(createMemoryHistory()),
    storeContents,
    middleware
  );

  if (dispatchMock) {
    store.dispatch = dispatchMock;
  }

  return render(
    <IntlProvider textComponent={React.Fragment} locale="en">
      <Provider store={store}>
        <MemoryRouter>{reactContent}</MemoryRouter>
      </Provider>
    </IntlProvider>
  );
};

/*
  mountComponentForTesting:
  Fully renders a component tree for the passed JSX Element
*/
export const mountComponentForTesting = (
  reactContent: JSX.Element,
  storeContents = {},
  dispatchMock?: (...args: any[]) => any
) => {
  const middleware = applyMiddleware(thunk);

  const store = createStore(
    createRootReducer(createMemoryHistory()),
    storeContents,
    middleware
  );

  if (dispatchMock) {
    store.dispatch = dispatchMock;
  }

  return mount(
    <IntlProvider textComponent={React.Fragment} locale="en">
      <Provider store={store}>
        <MemoryRouter>{reactContent}</MemoryRouter>
      </Provider>
    </IntlProvider>
  );
};
