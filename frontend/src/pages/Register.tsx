import React, {
  useContext, useState,
} from 'react';
import { Redirect } from 'react-router-dom';
import { Input } from '../Components/Form/Input';
import { Label } from '../Components/Form/Label';
import { Fieldset } from '../Components/Form/Fieldset';
import { Error } from '../Components/Form/Error';
import { Button } from '../Components/Button/Button';
import { Direction } from '../types/direction';
import { globalContext } from '../store';

import { registerUser, getUser } from '../api/calls';

export default function Register() {
  const { dispatch } = useContext(globalContext);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [password2, setPassword2] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [loggedIn, setLoggedIn] = useState(false);
  const [errors, setErrors] = useState([]);

  const handleSubmit = async (e: any) => {
    e.preventDefault();
    setErrors([]);
    const token = await registerUser(email, password, password2, firstName, lastName).catch((err) => {
      const localErrors = [];
      if (err.response.status < 500) {
        for (const [key, value] of Object.entries(err.response.data)) {
          localErrors.push(`${key}: ${value}`);
        }
      }
      setErrors(localErrors);
      throw err;
    });
    if (token) {
      await dispatch({ type: 'SET_TOKEN', payload: token });
      const user = await getUser(token);
      await dispatch({ type: 'SET_USER', payload: user });
      setLoggedIn(true); // Setting the state to redirect after login
    }
  };

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
    return <Redirect to="/themas" />;
  }
  return (
    <>
      <div className="register">
        <h1>Registreer</h1>
        <form action="" onSubmit={handleSubmit}>
          {errors.map((object, i) => <Error key={i}>{ object }</Error>)}
          <Fieldset direction={Direction.Vertical}>
            <Label for="email">Emailadres</Label>
            <Input
              type="email"
              name="email"
              required
              value={email}
              changeAction={handleEmailChange}
            />
          </Fieldset>
          <Fieldset direction={Direction.Vertical}>
            <Label for="first_name">Voornaam</Label>
            <Input
              type="text"
              name="first_name"
              required
              value={firstName}
              changeAction={handleFirstNameChange}
            />
          </Fieldset>
          <Fieldset direction={Direction.Vertical}>
            <Label for="last_name">Acternaam</Label>
            <Input
              type="text"
              name="last_name"
              required
              value={lastName}
              changeAction={handleLastNameChange}
            />
          </Fieldset>
          <Fieldset direction={Direction.Vertical}>
            <Label for="password">Wachtwoord</Label>
            <Input
              type="password"
              name="password"
              required
              value={password}
              changeAction={handlePasswordChange}
            />
          </Fieldset>
          <Fieldset direction={Direction.Vertical}>
            <Label for="password2">Wachtwoord</Label>
            <Input
              type="password"
              name="password2"
              required
              value={password2}
              changeAction={handlePassword2Change}
            />
          </Fieldset>
          <Fieldset direction={Direction.Horizontal}>
            <Button type="submit">Registreer</Button>
            <Button href="/login" open>Terug naar login</Button>
          </Fieldset>
        </form>
      </div>
    </>
  );
}
