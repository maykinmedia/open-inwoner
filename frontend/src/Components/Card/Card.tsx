import React, {ReactElement} from 'react';
import {Link} from 'react-router-dom';
import {H4} from '../Typography/H4';
import './Card.scss';

interface iCardProps {
  header?: ReactElement,
  title: string,
  alt?: string,
  children?: any,
  src?: string,
  to?: string,
}


/**
 * A card.
 * @param {iCardProps} props
 * @return {ReactElement}
 */
export function Card(props: iCardProps): ReactElement {
  const {header, title, children, to, alt, src, ..._props} = props

  const Tag = (to) ? Link : (props: any) => <aside {...props}/>;

  return (
    <Tag className="card" to={to} {..._props}>
      {header || src && <header className="card__header">
        {src && <img className="card__img" src={src} alt={alt}/>}
        {header}
      </header>}

      <div className="card__body">
        <H4>{title}</H4>
        {children}
      </div>
    </Tag>
  );
}
