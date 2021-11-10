import React from 'react';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import FacebookIcon from '@mui/icons-material/Facebook';
import LinkedInIcon from '@mui/icons-material/LinkedIn';
import TwitterIcon from '@mui/icons-material/Twitter';
import {Logo} from '../Logo/Logo';
import './Footer.scss';
import {H4} from '../Typography/H4';
import {P} from '../Typography/P';
import {Button} from '../Button/Button';
import {RouteLink} from '../Typography/RouteLink';
import {ROUTES} from '../../routes/routes';
import {Link} from '../Typography/Link';

export const Footer = () => {
  return (
    <footer className='footer'>
      <Logo/>

      <aside className="footer__visitor">
        <H4>Bezoekadres</H4>
        <P>Stadhuis Spui (stadsdeelkantoor Centrum)<br/>
          Spui 70, 2511 BT Den Haag</P>
        <Button icon={ArrowForwardIcon} transparent={true}>Bekijk op Google Maps</Button>
      </aside>

      <aside className="footer__mail">
        <H4>Postadres</H4>
        <P>Gemeente Den Haag<br/>
          Postbus 12 600<br/>
          2500 DJ Den Haag</P>
      </aside>

      <aside className="footer__social">
        <H4>Op social media</H4>
        <Link to="#" icon={FacebookIcon}></Link>
        <Link to="#" icon={TwitterIcon}></Link>
        <Link to="#" icon={LinkedInIcon}></Link>
      </aside>

      <aside className="footer__newsletter">
        <H4>Meld je aan voor de nieuwsbrief</H4>
        <Button>Aanmelden</Button>
      </aside>

      <nav className="footer__links">
        <ul className="footer__list">
          <li className="footer__list-item"><RouteLink primary={true} route={ROUTES.PRIVACY_STATEMENT}/></li>
          <li className="footer__list-item"><RouteLink primary={true} route={ROUTES.COOKIE_STATEMENT}/></li>
          <li className="footer__list-item"><RouteLink primary={true} route={ROUTES.ACCESSIBILITY_STATEMENT}/></li>
          <li className="footer__list-item"><RouteLink primary={true} route={ROUTES.PERSONAL_DATA}/></li>
          <li className="footer__list-item"><RouteLink primary={true} route={ROUTES.TERMS_AND_CONDITIONS}/></li>
          <li className="footer__list-item"><RouteLink primary={true} route={ROUTES.PROCLAIMER}/></li>
          <li className="footer__list-item"><RouteLink primary={true} route={ROUTES.DISCLAIMER}/></li>
        </ul>
      </nav>
    </footer>
  );
}
