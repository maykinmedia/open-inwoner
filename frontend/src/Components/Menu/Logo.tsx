import React from 'react';
import { Link } from 'react-router-dom';

interface LogoProps {
    src: string,
    alt: string,
}

export function Logo(props:LogoProps) {
  return (
    <Link to="/">
      <img className="menu__logo" src={props.src} alt={props.alt} />
    </Link>
  );
}
