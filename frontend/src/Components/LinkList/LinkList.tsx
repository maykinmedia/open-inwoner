import React, { ReactElement } from 'react';

import { Link } from 'react-router-dom'

import './LinkList.scss'

interface iLinkForList {
  name: string,
  href: string,
  type: string,
}

interface iLinkListProps {
  links: Array<iLinkForList>,
}

export function LinkList(props: iLinkListProps) {
  return (
    <ul className="link-list">
      {props.links.map((link, index) => <li key={ index }><Link to={link.href}>{link.name}</Link></li>)}
    </ul>
  );
}
