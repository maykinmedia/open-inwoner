import React from 'react';
import Scrollspy from 'react-scrollspy';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';

import './AnchorMenu.scss';

export default function AnchorMenu() {
  return (
    <Scrollspy className="anchor-menu" items={['title', 'files', 'links', 'see', 'share']} currentClassName="anchor-menu__item--highlight">
      <li className="anchor-menu__item"><a className="anchor-menu__link" href="#title">Persoonlijk Plan</a></li>
      <li className="anchor-menu__item"><a className="anchor-menu__link" href="#files">Bestanden</a></li>
      <li className="anchor-menu__item"><a className="anchor-menu__link" href="#links">Links</a></li>
      <li className="anchor-menu__item"><a className="anchor-menu__link" href="#see">Zie ook</a></li>
      <li className="anchor-menu__item"><a className="anchor-menu__link" href="#share">Delen</a></li>
      <li className="anchor-menu__item anchor-menu__item--top">
        <a className="anchor-menu__link" href="#title">
          <ArrowUpwardIcon className="anchor-menu__icon" />
          Terug naar boven
        </a>
      </li>
    </Scrollspy>
  );
}
