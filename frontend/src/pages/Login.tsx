import React, { Component, useContext, Dispatch, useState } from 'react';
import { Redirect } from 'react-router-dom'
import { Input } from '../Components/Form/Input'
import { Label } from '../Components/Form/Label'
import { Fieldset } from '../Components/Form/Fieldset'
import { Button } from '../Components/Button/Button'
import { Direction } from '../Enums/direction'
import { globalContext } from '../store';
import { Token } from '../store/types';

import axios from 'axios';


export default function Login() {
    const { globalState, dispatch } = useContext(globalContext);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loggedIn, setLoggedIn] = useState(false);
    const [errors, setErrors] = useState([]);

    const handleSubmit = async (e: any) => {
        e.preventDefault();
        const token = await loginUser(email, password);
        if (token) {
            await dispatch({ type: 'SET_TOKEN', payload: token })
            const user = await getUser(token);
            await dispatch({ type: 'SET_USER', payload: user })
            setLoggedIn(true); // Setting the state to redirect after login
        }
    }

    const loginUser = async (email?: string, password?: string) => {
        try {
            const res = await axios.post('http://localhost:8000/api/auth/login/', {email: email, password: password}).catch(err => {
                console.log(err.response.data)
                setErrors(err.response.data);
                throw err;
              });
            return res.data;
          } catch(err) {
              console.log(err)
          }
    }

    const getUser = async (token: Token) => {
        return fetch('http://localhost:8000/api/auth/user/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Token ${token.key}`,
            },
        })
        .then(data => data.json())
        .catch(error => dispatch({type: "SET_ERROR", payload: error}))
    }

    function handleEmailChange(event: React.ChangeEvent<HTMLInputElement>) {
        setEmail(event.currentTarget.value);
    }

    function handlePasswordChange(event: React.ChangeEvent<HTMLInputElement>) {
        setPassword(event.currentTarget.value);
    }

    if (loggedIn) {
        return <Redirect to='/'/>
    }
    return (
        <>
            <div className="login">
                <h1>Login</h1>
                <form action="" onSubmit={handleSubmit}>
                    <Fieldset direction={ Direction.Vertical }>
                        <Label for="email">Emailadres</Label>
                        <Input
                            type="email"
                            name="email"
                            required={true}
                            value={email}
                            changeAction={handleEmailChange}
                        />
                    </Fieldset>
                    <Fieldset direction={ Direction.Vertical }>
                        <Label for="password">Wachtwoord</Label>
                        <Input
                            type="password"
                            name="password"
                            required={true}
                            value={password}
                            changeAction={handlePasswordChange}
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
