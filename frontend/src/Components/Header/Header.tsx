import React, {useContext, useEffect, useState} from 'react';
import {logout} from '../../api/calls';
import {ROUTES} from '../../routes/routes';
import {globalContext} from '../../store';
import {Breadcrumbs} from './Breadcrumbs';
import {Logo} from '../Logo/Logo';
import PrimaryNavigation from './PrimaryNavigation';
import {RouteLink} from '../Typography/RouteLink';
import {P} from '../Typography/P';
import './Header.scss';


/**
 * Renders the header including all the navigation.
 * @return {ReactElement}
 */
export function Header() {
  const {globalState, dispatch} = useContext(globalContext);
  const [greeting, setGreeting] = useState('Welkom');

  useEffect(() => {
    setGreeting(`Welkom ${globalState?.user?.firstName} ${globalState.user?.lastName}`.trim());
  }, [globalState])

  /**
   * Logout.
   */
  async function handleLogout() {
    await logout();
    await dispatch({type: 'PURGE_STATE'});
  }

  /**
   * Returns the welcome message.
   * @return {ReactElement}
   */
  const getWelcomeMessage = () => {
    return (
      <P>{greeting}</P>
    )
  };

  /**
   * Returns the login/logout link(s).
   * @return {ReactElement}
   */
  const getLoginLinks = () => {
    if (globalState?.user) {
      return (
        <ul className="header__list">
          <li className="header__list-item">
            <RouteLink onClick={handleLogout} route={ROUTES.LOGOUT}/>
          </li>
        </ul>
      );
    }

    return (
      <ul className="header__list">
        <li className="header__list-item">
          <RouteLink route={ROUTES.REGISTER}/>
        </li>

        <li className="header__list-item">
          <RouteLink primary={true} route={ROUTES.LOGIN}/>
        </li>
      </ul>
    );
  };

  return (
    <header className="header">
      <Logo/>

      <nav className="header__actions">
        {getWelcomeMessage()}
        {getLoginLinks()}
      </nav>

      <PrimaryNavigation/>
      <Breadcrumbs/>
    </header>
  );
}
