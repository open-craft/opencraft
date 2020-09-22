import { ConnectedRouter } from 'connected-react-router';
import { history } from 'global/history';
import React from 'react';
import ReactDOM from 'react-dom';
import { IntlProvider } from 'react-intl';
import { Provider } from 'react-redux';
import { store } from './global/store';
import * as serviceWorker from './serviceWorker';
import '@fortawesome/fontawesome-free/css/all.min.css';
import './styles/app.scss';
import { App } from './ui/components';
import { MatomoTracker } from './utils/MatomoTracker';

ReactDOM.render(
  <MatomoTracker>
    <IntlProvider locale="en" textComponent={React.Fragment}>
      <Provider store={store}>
        <ConnectedRouter history={history}>
          <App />
        </ConnectedRouter>
      </Provider>
    </IntlProvider>
  </MatomoTracker>,
  document.getElementById('root')
);

// If you want your App to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister();
