import React, {useContext} from 'react';
import { Link } from 'react-router-dom';

import {globalContext} from '../../store';

import './Logo.scss';

export function Logo() {
  const { globalState } = useContext(globalContext);

  const getLogo = () => {
    if (globalState?.logo) {
      return `${globalState?.logo.url}`
    }
    return undefined
  }

  if (!globalState) {
    return <></>
  }

  return (
    <Link className="logo" to="/">
      <img className="logo__image" src={getLogo()} alt={ globalState?.logo?.description }/>
    </Link>
  );
}
