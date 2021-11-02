import { useContext } from 'react';
import { Switch, useLocation } from 'react-router-dom';
import { GuardProvider, GuardedRoute } from 'react-router-guards';

import { getToken, getUser } from '../api/calls';

import Home from '../pages/Home';
import NotFoundPage from '../pages/NotFound';
import About from '../pages/About';
import Login from '../pages/Login';
import Register from '../pages/Register';
import Themas from '../pages/Themas/index';
import ThemeDetail from '../pages/Themas/detail';
import ProductDetail from '../pages/Product/detail';
import { globalContext } from '../store';
import { getIsLoggedIn } from '../utils';

export function RouterView() {
  const { globalState, dispatch } = useContext(globalContext);
  const location = useLocation();
  const { pathname } = location;

  const requireLogin = (to, from, next) => {
    if (to.meta.auth) {
      if (getIsLoggedIn(globalState)) {
        next();
      }
      next.redirect('/login');
    } else {
      next();
    }
  };

  function getCookie(cookieName:string) {
    const name = `${cookieName}=`;
    const decodedCookie = decodeURIComponent(document.cookie);
    const ca = decodedCookie.split(';');
    for (let i = 0; i < ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) == ' ') {
        c = c.substring(1);
      }
      if (c.indexOf(name) == 0) {
        return c.substring(name.length, c.length);
      }
    }
    return '';
  }

  const hasSession = async (to, from, next) => {
    const sessionCookie = getCookie('open_inwoner_sessionid');
    if (sessionCookie && !getIsLoggedIn(globalState)) {
      const token = await getToken();
      if (token) {
        await dispatch({ type: 'SET_TOKEN', payload: token });
        const user = await getUser(token);
        await dispatch({ type: 'SET_USER', payload: user });
      }
    }
    next();
  };

  return (
    <GuardProvider guards={[requireLogin, hasSession]} error={NotFoundPage}>
      <Switch>
        <GuardedRoute path="/" exact component={Home} />
        <GuardedRoute path="/login" exact component={Login} />
        <GuardedRoute path="/register" exact component={Register} />
        <GuardedRoute path="/themas" exact component={Themas} />
        <GuardedRoute path="/themas/:slug" exact component={ThemeDetail} />
        <GuardedRoute path="/product/:slug" exact component={ProductDetail} />
        <GuardedRoute path="/about" exact component={About} meta={{ auth: true }} />
        <GuardedRoute path="*" component={NotFoundPage} />
      </Switch>
    </GuardProvider>
  );
}
