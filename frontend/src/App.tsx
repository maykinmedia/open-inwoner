import React, { useEffect, useContext } from 'react';
import {AccessibilityHeader} from './Components/AccessibilityHeader/AccessibilityHeader';
import {Container} from './Components/Container/Container';
import {Footer} from './Components/Footer/Footer';
import {Header} from './Components/Header/Header'
import { RouterView } from './routes/RouterView';
import { getConfiguration } from './api/calls';
import {globalContext} from './store';

import './fonts/TheMixC5/DesktopFonts/TheMixC5-5_Plain.otf';
import './fonts/TheSansC5/DesktopFonts/TheSansC5-5_Plain.otf';
import './App.scss';

export function App() {
  const { dispatch } = useContext(globalContext);

  useEffect(() => {
    const load = async () => {
      const configuration = await getConfiguration();

      // Set the new settings to the document.
      let root = document.documentElement;
      root.style.setProperty('--color-primary', configuration.primaryColor);
      root.style.setProperty('--color-secondary', configuration.secondaryColor);
      root.style.setProperty('--color-accent', configuration.accentColor);

      // Store logo in general state.
      await dispatch({type: 'SET_LOGO', payload: configuration.logo});
    };
    load();
  }, []);

  return (
    <>
      <AccessibilityHeader/>
      <Header/>
      <Container>
        <RouterView/>
      </Container>
      <Footer/>
    </>
  );
}
