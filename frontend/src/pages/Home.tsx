import React from 'react';
import { Grid } from '../Components/Container/Grid';

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
