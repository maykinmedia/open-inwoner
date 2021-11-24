import React from 'react';
import { Link } from 'react-router-dom';

import { H1 } from '../Components/Typography/H1'

export default function NotFoundPage() {
  return (
    <>
      <div>
        <H1>Pagina niet gevonden</H1>
        <Link to="/">Terug naar de homepagina</Link>
      </div>
    </>
  );
}
