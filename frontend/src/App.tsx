import React, { useContext } from 'react';
import { NavLink } from 'react-router-dom';
import { Menu } from './Components/Menu/Menu';
import { Logo } from './Components/Menu/Logo';
import { MenuText } from './Components/Menu/MenuText';
import { Container } from './Components/Container/Container';

import { logout } from './api/calls';

import './App.scss';
import { globalContext } from './store';
import { RouterView } from './routes/RouterView';
import './fonts/TheMixC5/DesktopFonts/TheMixC5-5_Plain.otf';
import './fonts/TheSansC5/DesktopFonts/TheSansC5-5_Plain.otf';

export function App() {
  const { globalState, dispatch } = useContext(globalContext);

  async function handleLogout() {
    await logout();
    await dispatch({ type: 'PURGE_STATE' });
  }

  const getMenuText = () => {
    if (globalState.user) {
      return (
        <MenuText>
          Welkom
          {globalState.user.firstName}
          {' '}
          {globalState.user.lastName}
        </MenuText>
      );
    }
    return <></>;
  };

  const getLoginLink = () => {
    if (globalState.user) {
      return <NavLink className="menu__link menu__link--highlighted" activeClassName="menu__link--active" onClick={handleLogout} to="/">Logout</NavLink>;
    }
    return (
      <>
        <NavLink className="menu__link" activeClassName="menu__link--active" to="/register">Registreer</NavLink>
        <NavLink className="menu__link menu__link--highlighted" activeClassName="menu__link--active" to="/login">Login</NavLink>
      </>
    );
  };

  return (
    <>
      <Menu>
        <Logo src="https://www.zwolle.nl/sites/all/themes/custom/zwolle_redesign/logo.png" alt="Logo van gemeente" />
        <div className="menu__info">
          { getMenuText() }
          { getLoginLink() }
        </div>
      </Menu>
      <Container>
        <RouterView />
      </Container>
    </>
  );
}
