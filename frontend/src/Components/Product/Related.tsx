import React from 'react';
import { Link } from 'react-router-dom';

import './ProductLinks.scss';

interface iSmallProject {
    url: string,
    name: string,
    slug: string,
}

interface iRelatedProps {
    related?: Array<iSmallProject>
    id: string,
}

export function Related(props:iRelatedProps) {
  return (
    <div id={props.id} className="product-links">
      <h4 className="product-links__title">Zie ook</h4>
      {props.related?.map((related:iSmallProject) => (
        <Link key={related.slug} className="product-links__link" to={`/product/${related.slug}`}>{related.name}</Link>
      ))}
    </div>
  );
}
