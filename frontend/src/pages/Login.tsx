import React, { Component } from 'react';
import { Redirect } from 'react-router-dom'
import { Input } from '../Components/Form/Input'
import { Label } from '../Components/Form/Label'
import { Fieldset } from '../Components/Form/Fieldset'
import { Button } from '../Components/Button/Button'
import { Direction } from '../Enums/direction'

interface LoginProps {
    user: Object,
    token: {
        key: string,
    },
    setParentState: Function,
}

type LoginState = {
    loggedIn: boolean,
    email?: string,
    password?: string,
};

export default class Login extends Component<LoginProps, LoginState> {
    state: Readonly<LoginState> = {
        loggedIn: false,
        email: '',
        password: '',
    };

    handleSubmit = async (e: any) => {
        e.preventDefault();
        const localToken = await this.loginUser(this.state.email, this.state.password);
        console.log(localToken);
        this.props.setParentState({ token: localToken });
        const user = await this.getUser();
        this.props.setParentState({ user: user });
        // history.push("/about");
        this.setState({loggedIn: true})
        // TODO: Redirect to a personal page.
    }

    loginUser = async (email?: string, password?: string) => {
        return fetch('http://localhost:8000/api/auth/login/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({email: email, password: password})
        })
        .then(data => data.json())
    }

    getUser = async () => {
        return fetch('http://localhost:8000/api/auth/user/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Token ${this.props.token.key}`,
            },
        })
        .then(data => data.json())
    }

    setEmail = (event: any) => {
        this.setState({ email: event.target.value })
    }

    setPassword = (event: any) => {
        this.setState({ password: event.target.value })
    }

    render() {
        const { loggedIn } = this.state;

        if (loggedIn) {
            return <Redirect to='/about'/>
        }
        return (
            <>
                <div className="login">
                    <h1>Login</h1>
                    <form action="" onSubmit={this.handleSubmit}>
                        <Fieldset direction={ Direction.Vertical }>
                            <Label for="email">Emailadres</Label>
                            <Input
                                type="email"
                                name="email"
                                required={true}
                                value={this.state.email}
                                changeAction={this.setEmail}
                            />
                        </Fieldset>
                        <Fieldset direction={ Direction.Vertical }>
                            <Label for="password">Wachtwoord</Label>
                            <Input
                                type="password"
                                name="password"
                                required={true}
                                value={this.state.email}
                                changeAction={this.setPassword}
                            />
                        </Fieldset>
                        <Fieldset direction={ Direction.Horizontal }>
                            <Button type="submit">Login</Button>
                            <Button href="http://localhost:8000/digid/login/" open={true}>Login met Digid</Button>
                        </Fieldset>
                    </form>
                </div>
            </>
        )
    }
}
