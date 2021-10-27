import React, { ReactElement, useContext } from 'react';
import { HashRouter, Redirect, Route, Switch, useLocation } from 'react-router-dom';
import Home from '../pages/Home';
import About from '../pages/About';
import Login from '../pages/Login';
import Register from '../pages/Register';
import Themas from '../pages/Themas/index';
import ThemeDetail from '../pages/Themas/detail';
import { PrivateRoute } from './PrivateRoute';
import { globalContext } from '../store';

export function RouterView(): ReactElement {
    const { globalState } = useContext(globalContext);
    const location = useLocation();
    const { pathname } = location;

    return (
        <Switch>
            <Route exact path="/">
                <Home />
            </Route>
            <Route exact path="/register">
                <Register />
            </Route>
            <Route exact path="/themas">
                <Themas />
            </Route>
            <Route exact path="/themas/1">
                <ThemeDetail />
            </Route>
            <PrivateRoute exact path="/about" pathname={pathname} component={About} />
            {/* <Route exact path="/login">
                {globalState.user ? <Redirect to="/themas" from={pathname} /> : <Login />}
            </Route> */}
        </Switch>
    );
}
