import React, {useContext} from 'react';
import {Switch} from 'react-router-dom';
import {GuardProvider, GuardedRoute, Next} from 'react-router-guards';
import {GuardFunctionRouteProps, GuardToRoute} from 'react-router-guards/dist/types';
import {getToken, getUser} from '../api/calls';
import NotFoundPage from '../pages/NotFound';
import {globalContext} from '../store';
import {iToken} from '../store/types';
import {getIsLoggedIn} from '../utils';
import {ROUTES} from './routes';


export function RouterView() {
  const {globalState, dispatch} = useContext(globalContext);

  const requireLogin = (to: GuardToRoute, from: GuardFunctionRouteProps | null, next: Next) => {
    if (to.meta.auth) {
      if (getIsLoggedIn(globalState)) {
        next();
      }
      next.redirect('/login');
    } else {
      next();
    }
  };

  /**
   * Returns a cookie.
   * @param {string} cookieName
   * @return {string}
   */
  function getCookie(cookieName: string) {
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

  const hasSession = async (to: GuardToRoute, from: GuardFunctionRouteProps | null, next: Next) => {
    const sessionCookie = getCookie('open_inwoner_sessionid');
    if (sessionCookie && !getIsLoggedIn(globalState)) {
      const token = await getToken();
      if (token) {
        await dispatch({type: 'SET_TOKEN', payload: token});
        const user = await getUser(token as iToken);
        await dispatch({type: 'SET_USER', payload: user});
      }
    }
    next();
  };

  const renderRoutes = () => {
    return Object.entries(ROUTES).map(([key, route]) => (
      <GuardedRoute key={key} component={route.component} exact={route.exact} path={route.path}
                    meta={{auth: route.loginRequired}}/>
    ))
  };

  return (
    <GuardProvider guards={[requireLogin, hasSession]} error={NotFoundPage}>
      <Switch>
        {renderRoutes()}
      </Switch>
    </GuardProvider>
  );
}
