import React, { Component } from 'react';
import { Redirect } from 'react-router-dom'

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

    render() {
        const { loggedIn } = this.state;

        if (loggedIn) {
            return <Redirect to='/about'/>
        }
        return (
            <>
                <div className="card">
                    <h1>Login</h1>
                    <form action="" onSubmit={this.handleSubmit}>
                        <fieldset>
                            <label htmlFor="">Emailadres</label>
                            <input type="email" name="email" id="id_email" required onChange={e => this.setState({ email: e.target.value })} />
                        </fieldset>
                        <fieldset>
                            <label htmlFor="">Wachtwoord</label>
                            <input type="password" name="password" id="id_password" required onChange={e => this.setState({ password: e.target.value })} />
                        </fieldset>
                        <input type="submit" value="Login" />
                        <a href="http://localhost:8000/digid/login/">Login met Digid</a>
                    </form>
                </div>
            </>
        )
    }
}
