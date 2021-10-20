import { useState } from 'react'
import { Route, Switch } from 'react-router-dom'
import { Menu } from './Components/Menu/Menu'
import { Logo } from './Components/Menu/Logo'
import { MenuText } from './Components/Menu/MenuText'
import { NavLink } from "react-router-dom"

import './App.scss'

const pages = import.meta.globEager('./pages/*.tsx')
const routes = Object.keys(pages).map((path) => {
    console.log(path, pages[path].default);
    const name = path.match(/\.\/pages\/(.*)\.tsx$/)[1]
    console.log(name);
    return {
        name,
        path: name === '_Home' ? '/' : `/${name.toLowerCase()}`,
        component: pages[path].default
    }
})

export function App() {
    return (
        <>
            <Menu>
                <Logo src="https://www.zwolle.nl/sites/all/themes/custom/zwolle_redesign/logo.png" alt="Logo van gemeente"/>
                <div className="menu__info">
                    <MenuText>Welkom Anne Boersma</MenuText>
                    <NavLink className="menu__link" activeClassName="menu__link--active" to="/login">Login</NavLink>
                </div>
            </Menu>
            <Switch>
                {routes.map(({ path, component: RouteComp }) => {
                    return (
                        <Route key={path} path={path}>
                            <RouteComp />
                        </Route>
                    )
                })}
            </Switch>
        </>
    )
}
