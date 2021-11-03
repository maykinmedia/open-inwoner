import React from 'react';
import OpenInNewOutlinedIcon from '@mui/icons-material/OpenInNewOutlined';
import './ProductLinks.scss';

interface iLink {
    name: string,
    url: string,
}

interface LinkProps {
    id: string,
    links?: Array<iLink>;
}

export function Links(props:LinkProps) {
  return (
    <div id={props.id} className="product-links">
      <h4 className="product-links__title">Links</h4>
      {props.links?.map((link:iLink, index:Number) => (
        <a key={`${index}`} className="product-links__link" target="_blank" href={link.url} rel="noreferrer">
          {link.name}
          <OpenInNewOutlinedIcon className="product-links__icon" />
        </a>
      ))}
    </div>
  );
}
