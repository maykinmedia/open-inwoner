import React, { useContext } from 'react';
import { Link } from 'react-router-dom';
import { globalContext } from '../../store';
import './SideMenu.scss';

export default function SideMenu() {
  const { globalState } = useContext(globalContext);
  return (
    <div className="side-menu">
      <Link className="side-menu__link" to="/">Overzicht</Link>
      {globalState.user
                && (
                <>
                  <li><Link className="side-menu__link" to="/">Mijn berichten</Link></li>
                  <li><Link className="side-menu__link" to="/">Mijn Profiel</Link></li>
                </>
                )}
      <Link className="side-menu__link" to="/themas">Themas</Link>
      <Link className="side-menu__link" to="/">Samenwerken</Link>
      <Link className="side-menu__link" to="/">Zelfdiagnose</Link>
    </div>
  );
}
