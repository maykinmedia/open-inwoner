import React, {ReactElement, SyntheticEvent, useContext, useState} from 'react';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import {iButtonProps} from '../Components/Button/Button';
import {Form} from '../Components/Form/Form';
import {Grid} from '../Components/Container/Grid';
import {H1} from '../Components/Typography/H1';
import {ROUTES} from '../routes/routes';
import {globalContext} from '../store';
import {iField} from '../types/field';
import {iToken} from "../store/types";
import {getUser, registerUser} from "../api/calls";
import {P} from "../Components/Typography/P";

export default function Register() {
  const {dispatch} = useContext(globalContext);
  const [errors, setErrors] = useState<{ [index: string]: string[] }>({});
  const [registrationComplete, setRegistrationComplete] = useState<boolean|null>(null);

  const onSubmit = async (event: SyntheticEvent, data: { [index: string]: string }): Promise<void> => {
    const {email, first_name, last_name, password, password2} = data;
    setErrors({});

    event.preventDefault();

    const token: iToken | void = await registerUser(email, password, password2, first_name, last_name)
      .catch((err) => {
        const errors = err.response.data;
        setErrors(errors)
      });

    if (token) {
      await dispatch({type: 'SET_TOKEN', payload: token});
      const user = await getUser(token);
      await dispatch({type: 'SET_USER', payload: user});

      setRegistrationComplete(true);
    }

  };

  /**
   * Returns the additional form actions.
   */
  const getActions = (): iButtonProps[] => {
    return [{
      children: ROUTES.REGISTER.label,
      href: ROUTES.REGISTER.path,
      icon: ArrowForwardIcon,
      iconPosition: 'after',
      transparent: true
    }]
  }

  /**
   * Returns the fields for the form.
   * @return {iField[]}
   */
  const getFields = (): iField[] => [
    ['email', 'E-mail', 'email'],
    ['first_name', 'Voornaam', 'text'],
    ['last_name', 'Achternaam', 'text'],
    ['password', 'Wachtwoord', 'password'],
    ['password2', 'Wachtwoord (opnieuw)', 'password']
  ].map(([name, label, type]: string[]) => (
    {errors: errors[name] || [], label: label, name: name, type: type as any}
  ));

  /**
   * Returns the main content.
   * @return {ReactElement}
   */
  const getMainContent = (): ReactElement => (
    <>
      <H1>{ROUTES.REGISTER.label}</H1>

      {registrationComplete && <>
        <P>U bent nu geregistreerd.</P>
        <P>Er is een e-mail naar het door u opgegeven e-mail adres
          verstuurd met instructies hoe u uw account kunt activeren, u dient uw account te activeren voordat u kunt inloggen.</P>
      </>}

      {!registrationComplete &&
      <Form actions={getActions()} fields={getFields()} errors={errors.nonFieldErrors} submitLabel={ROUTES.REGISTER.label as string} onSubmit={onSubmit}/>}
    </>
  );

  return (
    <Grid mainContent={getMainContent()}/>
  );
}
