import React from 'react';

import { Link } from 'react-router-dom'
import { H1 } from '../Typography/H1'

import './LinkList.scss'

interface iLinkForList {
  name: string,
  intro: string,
  href: string,
  type: string,
}

interface iLinkListProps {
  count: number,
  links: Array<iLinkForList>,
}

export function LinkList(props: iLinkListProps) {
  const getResult = (link:iLinkForList, index:number) => {
    return (
      <Link className="search-results__item" key={index} to={link.href}>
        <p className="search-results__item-title">{link.name}</p>
        <div className="search-results__item-info-container">
          <p className="search-results__item-intro">{link.intro}</p>
          <p className="search-results__item-type">{link.type}</p>
        </div>
      </Link>
    )
  }

  return (
    <div className="search-results">
      <H1 className="search-results__title">Zoekresultaten<span className="search-results__title-small">{ props.count } zoekresultaten</span></H1>
      <div className="search-results__list">
        {props.links.map((link, index) => getResult(link, index))}
      </div>
    </div>
  );
}
