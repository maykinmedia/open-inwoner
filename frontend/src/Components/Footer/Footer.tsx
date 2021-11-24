import React from 'react';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import {Logo} from '../Logo/Logo';
import {H4} from '../Typography/H4';
import {P} from '../Typography/P';
import {Button} from '../Button/Button';
import {RouteLink} from '../Typography/RouteLink';
import {ROUTES} from '../../routes/routes';
import {Social} from '../Social/Social';
import './Footer.scss';


export const Footer = () => {
  return (
    <footer className='footer'>
      <Logo/>

      <aside className="footer__visitor">
        <H4>Bezoekadres</H4>
        <P>Stadhuis Spui (stadsdeelkantoor Centrum)<br/>
          Spui 70, 2511 BT Den Haag</P>
        <Button icon={ArrowForwardIcon} iconPosition='before' transparent={true}>Bekijk op Google Maps</Button>
      </aside>

      <aside className="footer__mail">
        <H4>Postadres</H4>
        <P>Gemeente Den Haag<br/>
          Postbus 12 600<br/>
          2500 DJ Den Haag</P>
      </aside>

      <Social primary={true}/>

      <aside className="footer__newsletter">
        <H4>Meld je aan voor de nieuwsbrief</H4>
        <Button primary={true}>Aanmelden</Button>
      </aside>

      <nav className="footer__links">
        <ul className="footer__list">
          <li className="footer__list-item"><RouteLink secondary={true} route={ROUTES.PRIVACY_STATEMENT}/></li>
          <li className="footer__list-item"><RouteLink secondary={true} route={ROUTES.COOKIE_STATEMENT}/></li>
          <li className="footer__list-item"><RouteLink secondary={true} route={ROUTES.ACCESSIBILITY_STATEMENT}/></li>
          <li className="footer__list-item"><RouteLink secondary={true} route={ROUTES.PERSONAL_DATA}/></li>
          <li className="footer__list-item"><RouteLink secondary={true} route={ROUTES.TERMS_AND_CONDITIONS}/></li>
          <li className="footer__list-item"><RouteLink secondary={true} route={ROUTES.PROCLAIMER}/></li>
          <li className="footer__list-item"><RouteLink secondary={true} route={ROUTES.DISCLAIMER}/></li>
        </ul>
      </nav>
    </footer>
  );
}
