import { Component } from 'react'
import { Route, Switch, NavLink } from 'react-router-dom'
import { Menu } from './Components/Menu/Menu'
import { Logo } from './Components/Menu/Logo'
import { MenuText } from './Components/Menu/MenuText'
import { Container } from './Components/Container/Container'

import './App.scss'

const pages = import.meta.globEager('./pages/**/*.tsx')
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

type AppState = {
    token: {
        key: string,
    },
    user: {
        firstName: string,
        lastName: string,
        email: string,
    },
}

export class App extends Component<{}, AppState> {
    state: Readonly<AppState> = {
        token: {
            key: '',
        },
        user: {
            firstName: "",
            lastName: "",
            email: "",
        },
    };

    updateState = (toUpdate: any) => {
        this.setState(toUpdate);
    }

    getMenuText = () => {
        if (this.state.user.firstName) {
            return `Welkom ${this.state.user.firstName} ${this.state.user.lastName}`
        }
        return "";
    }

    getLoginLink = () => {
        if (this.state.user.firstName) {
            <NavLink className="menu__link menu__link--highlighted" activeClassName="menu__link--active" to="/logout">Logout</NavLink>
        }
        return (
            <NavLink className="menu__link menu__link--highlighted" activeClassName="menu__link--active" to="/login">Login</NavLink>
        )
    }

    render() {
        return (
            <>
                <Menu>
                    <Logo src="https://www.zwolle.nl/sites/all/themes/custom/zwolle_redesign/logo.png" alt="Logo van gemeente" />
                    <div className="menu__info">
                        <MenuText>{this.getMenuText()}</MenuText>
                        { this.getLoginLink() }
                    </div>
                </Menu>
                <Container>
                    <Switch>
                        {routes.map(({ path, component: RouteComp }) => {
                            return (
                                <Route key={path} path={path}>
                                    <RouteComp token={this.state.token} user={this.state.user} setParentState={this.updateState} />
                                </Route>
                            )
                        })}
                    </Switch>
                </Container>
            </>
        )
    }
}
