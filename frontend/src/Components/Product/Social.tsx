import { useContext } from 'react';
import { Link } from 'react-router-dom';
import FacebookOutlinedIcon from '@mui/icons-material/FacebookOutlined';
import TwitterIcon from '@mui/icons-material/Twitter';
import WhatsAppIcon from '@mui/icons-material/WhatsApp';
import LinkedInIcon from '@mui/icons-material/LinkedIn';
import { globalContext } from '../../store';

import './SocialLinks.scss';

interface iSocialProps {
    id: string,
}

export function Social(props:iSocialProps) {
  const { globalState, dispatch } = useContext(globalContext);
  return (
    <div id={props.id} className="social-links">
      <h4 className="social-links__title">Delen</h4>
      <div className="social-links__container">
        <Link className="social-links__link" to="#">
          <FacebookOutlinedIcon className="social-links__icon" />
        </Link>
        <Link className="social-links__link" to="#">
          <TwitterIcon className="social-links__icon" />
        </Link>
        <Link className="social-links__link" to="#">
          <WhatsAppIcon className="social-links__icon" />
        </Link>
        <Link className="social-links__link" to="#">
          <LinkedInIcon className="social-links__icon" />
        </Link>
      </div>
    </div>
  );
}
