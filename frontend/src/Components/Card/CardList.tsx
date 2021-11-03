import React from 'react';
import { CategoryCard } from './CategoryCard';
import { ProductCard } from './ProductCard';

import './CardList.scss';

interface CardListProps {
    title?: string,
    products?: Array<any>,
    categories?: Array<any>,
}

export function CardList(props:CardListProps) {
  const getCategories = () => {
    if (props.categories) {
      return (
        <div className="card-list" style={{ '--columns': '4' }}>
          {props.categories?.map((category) => <CategoryCard key={category.slug} to={`/themas/${category.slug}`} title={category.name} products={category.product} />)}
        </div>
      );
    }
    return null;
  };

  const getProducts = () => {
    if (props.products) {
      return (
        <div className="card-list">
          {props.products?.map((product) => <ProductCard key={product.slug} to={`/product/${product.slug}`} title={product.name} summary={product.summary} />)}
        </div>
      );
    }
    return null;
  };

  return (
    <>
      { getCategories() }
      { getProducts() }
    </>
  );
}
