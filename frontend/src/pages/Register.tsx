import React, { Component, useContext, Dispatch, useState } from 'react';
import { Redirect } from 'react-router-dom'
import { Input } from '../Components/Form/Input'
import { Label } from '../Components/Form/Label'
import { Fieldset } from '../Components/Form/Fieldset'
import { Error } from '../Components/Form/Error'
import { Button } from '../Components/Button/Button'
import { Direction } from '../Enums/direction'
import { globalContext } from '../store';
import { Token } from '../store/types';

import axios from 'axios';


export default function Register() {
    const { globalState, dispatch } = useContext(globalContext);
    const [email, setEmail] = useState('jorik.kraaikamp@gmail.com');
    const [password, setPassword] = useState('Pi22nguin37!');
    const [password2, setPassword2] = useState('Pi22nguin37!');
    const [firstName, setFirstName] = useState('Jorik');
    const [lastName, setLastName] = useState('Kraaikamp');
    const [loggedIn, setLoggedIn] = useState(false);
    const [errors, setErrors] = useState([]);

    const handleSubmit = async (e: any) => {
        e.preventDefault();
        const token = await registerUser(email, password, password2, firstName, lastName);
        console.log(token)
        // if (token) {
        //     await dispatch({ type: 'SET_TOKEN', payload: token })
        //     const user = await getUser(token);
        //     await dispatch({ type: 'SET_USER', payload: user })
        //     setLoggedIn(true); // Setting the state to redirect after login
        // }
    }

    const registerUser = async (email?: string, password1?: string, password2?: string, firstName?: string, lastName?: string) => {
        try {
            const res = await axios.post(`${import.meta.env.VITE_API_URL}/api/auth/registration/`, {email: email, password1: password1, password2: password2, firstName: firstName, lastName: lastName}).catch(err => {
                console.log(err.response.data)
                let localErrors = []
                for (const [key, value] of Object.entries(err.response.data)) {
                    localErrors.push(`${key}: ${value}`);
                }
                setErrors(localErrors);
                throw err;
              });
            return res.data;
          } catch(err) {
              console.log(err)
          }
    }

    function handleEmailChange(event: React.ChangeEvent<HTMLInputElement>) {
        setEmail(event.currentTarget.value);
    }

    function handlePasswordChange(event: React.ChangeEvent<HTMLInputElement>) {
        setPassword(event.currentTarget.value);
    }

    function handlePassword2Change(event: React.ChangeEvent<HTMLInputElement>) {
        setPassword2(event.currentTarget.value);
    }

    function handleFirstNameChange(event: React.ChangeEvent<HTMLInputElement>) {
        setFirstName(event.currentTarget.value);
    }

    function handleLastNameChange(event: React.ChangeEvent<HTMLInputElement>) {
        setLastName(event.currentTarget.value);
    }

    if (loggedIn) {
        return <Redirect to='/login'/>
    }
    return (
        <>
            <div className="register">
                <h1>Registreer</h1>
                <form action="" onSubmit={handleSubmit}>
                    {errors.map((object, i) => <Error key={i}>{ object }</Error>)}
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
                        <Label for="first_name">Voornaam</Label>
                        <Input
                            type="text"
                            name="first_name"
                            required={true}
                            value={firstName}
                            changeAction={handleFirstNameChange}
                        />
                    </Fieldset>
                    <Fieldset direction={ Direction.Vertical }>
                        <Label for="last_name">Acternaam</Label>
                        <Input
                            type="text"
                            name="last_name"
                            required={true}
                            value={lastName}
                            changeAction={handleLastNameChange}
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
                    <Fieldset direction={ Direction.Vertical }>
                        <Label for="password2">Wachtwoord</Label>
                        <Input
                            type="password"
                            name="password2"
                            required={true}
                            value={password2}
                            changeAction={handlePassword2Change}
                        />
                    </Fieldset>
                    <Fieldset direction={ Direction.Horizontal }>
                        <Button type="submit">Registreer</Button>
                        <Button href="/login" open={true}>Terug naar login</Button>
                    </Fieldset>
                </form>
            </div>
        </>
    )
}
