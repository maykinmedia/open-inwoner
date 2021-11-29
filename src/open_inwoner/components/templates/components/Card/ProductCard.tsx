import React from 'react';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import { Button } from '../Button/Button';
import { P } from '../Typography/P';
import { H3 } from '../Typography/H3';
import './Card.scss';

interface ProductCardProps {
    title: string,
    to: string,
    summary: string,
}

export function ProductCard(props:ProductCardProps) {
  return (
    <div className="card card--product">
      <H3>{ props.title }</H3>
      <P>{ props.summary }</P>
      <Button href={`/product/${props.to}`} transparent>
        <ArrowForwardIcon />
      </Button>
    </div>
  );
}
