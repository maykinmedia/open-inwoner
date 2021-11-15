import React from 'react';
import { Grid } from '../Components/Container/Grid';

export default function Search() {
  const getRight = () => (
    <>
      Search
    </>
  );

  return (
    <Grid isLoggedIn mainContent={getRight()} />
  );
}
