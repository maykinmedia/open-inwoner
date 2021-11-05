import React from 'react';
import { Grid } from '../Components/Container/Grid';
import HeaderMenu from '../Components/Header/SideMenu';

export default function Home() {
  const getRight = () => (
    <>
      Home
    </>
  );

  return (
    <Grid isLoggedIn right={getRight()} />
  );
}
