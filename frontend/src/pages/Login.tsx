import React, {ReactElement, SyntheticEvent, useContext, useState} from 'react';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import {useHistory} from 'react-router-dom';
import {H1} from '../Components/Typography/H1';
import {P} from '../Components/Typography/P';
import {Form} from '../Components/Form/Form';
import {Grid} from '../Components/Container/Grid';
import {login, getUser} from '../api/calls';
import {ROUTES} from '../routes/routes';
import {globalContext} from '../store';
import {iToken} from '../store/types';
import {iField} from '../types/field';
import {iButtonProps} from "../Components/Button/Button";

export default function Login() {
  const {dispatch} = useContext(globalContext);
  const [errors, setErrors] = useState<{ email?: string[], password?: string[], nonFieldErrors?: string[] }>({});
  const history = useHistory();

  /**
   * Gets called when the form is submitted, attempts to log in.
   * @param {SyntheticEvent} event
   * @param {Object} data
   */
  const onSubmit = async (event: SyntheticEvent, data: { email: string, password: string }): Promise<void> => {
    const {email, password} = data;
    setErrors({});

    event.preventDefault()
    ;
    const token: iToken | void = await login(email, password)
      .catch((err) => {
        const errors = err.response.data;
        setErrors(errors)
      })

    if (!token) {
      return;
    }

    await dispatch({type: 'SET_TOKEN', payload: token});
    const user = await getUser(token);
    await dispatch({type: 'SET_USER', payload: user});
    history.push(ROUTES.HOME.path);
  };

  /**
   * Returns the additional form actions.
   */
  const getActions = (): iButtonProps[] => {
    return [{children: ROUTES.REGISTER.label, href: ROUTES.REGISTER.path, icon: ArrowForwardIcon, iconPosition: 'after', transparent: true}]
  }

  /**
   * Returns the fields for the form.
   * @return {iField[]}
   */
  const getFields = (): iField[] => [
    {errors: errors.email || [], label: 'E-mail', name: 'email', type: 'text'},
    {label: 'Wachtwoord', name: 'password', type: 'password'},
  ];

  /**
   * Returns the main content.
   * @return {ReactElement}
   */
  const getMainContent = (): ReactElement => (
    <>
      <H1>Welkom</H1>
      <P>Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus.</P>
      <Form actions={getActions()} fields={getFields()} errors={errors.nonFieldErrors} submitLabel='Inloggen' onSubmit={onSubmit}></Form>
    </>
  );

  return (
    <Grid isLoggedIn mainContent={getMainContent()}/>
  );
}
