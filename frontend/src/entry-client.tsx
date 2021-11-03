import React from 'react';
import ReactDOM from 'react-dom';
import { BrowserRouter } from 'react-router-dom';
import { GlobalStore } from './store';
import { App } from './App';

ReactDOM.hydrate(
  <BrowserRouter>
    <GlobalStore>
      <App />
    </GlobalStore>
  </BrowserRouter>,
  document.getElementById('app'),
);
