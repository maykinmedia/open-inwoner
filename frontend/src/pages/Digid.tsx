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

    const handleSubmit = async () => {
        const token = await getToken();
        if (token) {
            await dispatch({ type: 'SET_TOKEN', payload: token })
            const user = await getUser(token);
            await dispatch({ type: 'SET_USER', payload: user })
            setLoggedIn(true); // Setting the state to redirect after login
        }
    }

    const getToken = async () => {
        console.log("Get token from cookie");
        return null;
    }

    const getUser = async (token: Token) => {
        return fetch(`${import.meta.env.VITE_API_URL}/api/auth/user/`, {
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
        return <Redirect to='/themas'/>
    }
    handleSubmit();
    return <></>
}
