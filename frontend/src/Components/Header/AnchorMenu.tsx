import React, {ReactElement} from 'react';
import Scrollspy from 'react-scrollspy';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import {iLinkProps, Link} from '../Typography/Link';
import './AnchorMenu.scss';


interface iAnchorMenuProps {
  links: iLinkProps[]
}

export default function AnchorMenu(props: iAnchorMenuProps): ReactElement {
  const {links, ..._props} = props;
  const items = links.map((linkProps: iLinkProps) => linkProps.to.replace('#', ''));

  const renderListItems = (): ReactElement[] => links.map((linkProps: iLinkProps): ReactElement => (
    <li key={linkProps.to} className="anchor-menu__list-item">
      <Link {...linkProps}/>
    </li>
  ))

  return (
    <aside className="anchor-menu" {..._props}>
      <Scrollspy className="anchor-menu__list" currentClassName="anchor-menu__list-item--active" items={items}>
        {renderListItems()}
        <li className="anchor-menu__list-item anchor-menu__list-item--top">
          <Link primary={true} to={(links.length) ? links[0].to : ''} icon={ArrowUpwardIcon}>Terug naar boven</Link>
        </li>
      </Scrollspy>
    </aside>
  );
}

AnchorMenu.defaultProps = {
  links: [],
}
