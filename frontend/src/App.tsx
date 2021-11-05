import React from 'react';
import {Header} from './Components/Header/Header'
import {Container} from './Components/Container/Container';
import {RouterView} from './routes/RouterView';
import './fonts/TheMixC5/DesktopFonts/TheMixC5-5_Plain.otf';
import './fonts/TheSansC5/DesktopFonts/TheSansC5-5_Plain.otf';
import './App.scss';

export function App() {
  return (
    <>
      <Header>

        <div className="menu__info">

        </div>
      </Header>
      <Container>
        <RouterView/>
      </Container>
    </>
  );
}
