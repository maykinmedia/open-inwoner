import React, {ReactElement} from 'react';
import {Link} from 'react-router-dom';
import FacebookOutlinedIcon from '@mui/icons-material/FacebookOutlined';
import TwitterIcon from '@mui/icons-material/Twitter';
import WhatsAppIcon from '@mui/icons-material/WhatsApp';
import LinkedInIcon from '@mui/icons-material/LinkedIn';
import {H4} from '../Typography/H4';
import './Social.scss';

interface iSocialProps {
  id?: string,
  title: string,
  primary?: boolean,
}

/**
 * Social media links/share.
 * TODO: Implement links/sharing behaviour.
 * @param {iSocialProps} props
 * @return {ReactElement}
 */
export function Social(props: iSocialProps): ReactElement {
  const {id, primary, title, ..._props} = props;

  /**
   * Returns the classname.
   * @return {string}
   */
  const getClassName = () => {
    let className = "social";

    if (primary) {
      className += " social--primary";
    }

    return className;
  }

  return (
    <nav className={getClassName()} {..._props}>
      <H4 id={id}>{title}</H4>

      <Link className="social__link" to="#">
        <FacebookOutlinedIcon className="social__icon"/>
      </Link>
      <Link className="social__link" to="#">
        <TwitterIcon className="social__icon"/>
      </Link>
      <Link className="social__link" to="#">
        <WhatsAppIcon className="social__icon"/>
      </Link>
      <Link className="social__link" to="#">
        <LinkedInIcon className="social__icon"/>
      </Link>
    </nav>
  );
}

Social.defaultProps = {
  title: 'Delen',
}
