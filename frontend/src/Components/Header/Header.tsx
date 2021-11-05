import React, {useContext} from 'react';
import {NavLink} from "react-router-dom";
import {logout} from '../../api/calls';
import {globalContext} from '../../store';
import {Breadcrumbs} from './Breadcrumbs';
import {Logo} from './Logo';
import PrimaryNavigation from './PrimaryNavigation';
import './Header.scss';
import './Link.scss';


/**
 * Renders the header including all the navigation.
 * @return {JSX.Element}
 */
export function Header() {
  const {globalState, dispatch} = useContext(globalContext);

  /**
   * Logout.
   */
  async function handleLogout() {
    await logout();
    await dispatch({type: 'PURGE_STATE'});
  }

  /**
   * Returns the welcome message.
   * @return {JSX.Element}
   */
  const getWelcomeMessage = () => {
    return (
      <p className="link">
        {globalState.user && `Welkom ${globalState.user.firstName} ${globalState.user.lastName}`}
        {!globalState.user && 'Welkom'}
      </p>
    )
  };

  /**
   * Returns the login/logout link(s).
   * @return {JSX.Element}
   */
  const getLoginLinks = () => {
    if (globalState.user) {
      return (
        <ul className="header__list">
          <li className="header__list-item">
            <NavLink className="link" onClick={handleLogout} to="#">Uitloggen</NavLink>
          </li>
        </ul>
      );
    }

    return (
      <ul className="header__list">
        <li className="header__list-item">
          <NavLink className="link" to="/register">Registreren</NavLink>
        </li>

        <li className="header__list-item">
          <NavLink className="link link--primary" activeClassName="link--active" to="/login">Inloggen</NavLink>
        </li>
      </ul>
    );
  };

  return (
    <header className="header">
      <Logo src="https://www.zwolle.nl/sites/all/themes/custom/zwolle_redesign/logo.png" alt="Logo van gemeente"/>

      <nav className="header__actions">
        {getWelcomeMessage()}
        {getLoginLinks()}
      </nav>

      <PrimaryNavigation/>
      <Breadcrumbs/>
    </header>
  );
}
