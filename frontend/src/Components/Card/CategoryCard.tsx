import React from 'react';
import { Link } from 'react-router-dom';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import { iProduct } from '../../types/pdc';

import './Card.scss';

interface CategoryCardProps {
    title: string,
    to: string,
    products: Array<any>,
}

export function CategoryCard(props:CategoryCardProps) {
  return (
    <div className="card card--list">
      <h3 className="card__title">{ props.title }</h3>
      <div className="card__links">
        { props.products?.map((product:iProduct) => (
          <Link className="card__link" key={product.slug} to={`/product/${product.slug}`}>
            {product.name}
            <ChevronRightIcon />
          </Link>
        )) }
      </div>
    </div>
  );
}
