import React from 'react';
import { Link } from 'react-router-dom';
import './Card.scss';

interface CardProps {
    src: string,
    alt: string,
    title: string,
    to: string,
}

export function Card(props:CardProps) {
  return (
    <Link className="card" to={props.to}>
      <img className="card__img" src={props.src} alt={props.alt} />
      <h3 className="card__title">{ props.title }</h3>
    </Link>
  );
}
