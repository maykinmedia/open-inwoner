import React, {useState, useEffect} from 'react';
import {useParams} from 'react-router-dom';
import {getCategory} from '../../api/calls';
import {Grid} from '../../Components/Container/Grid';
import {H1} from '../../Components/Typography/H1';
import {P} from '../../Components/Typography/P';
import {CardContainer} from '../../Components/CardContainer/CardContainer';
import { CategoryCard } from '../../Components/Card/CategoryCard';
import {ProductCard} from '../../Components/Card/ProductCard';

import { iCategory, iSmallProduct } from '../../types/pdc';

import './CategoryDetail.scss';

/**
 * Category detail.
 * @constructor
 */
export default function CategoryDetail() {
  const [category, setCategory] = useState<iCategory | null>(null);
  const {categorySlug} = useParams<{ [index: string]: string }>();

  useEffect(() => {
    const load = async () => {
      const resCategory = await getCategory(categorySlug);
      setCategory(resCategory);
    };
    load();
  }, []);

  /**
   * Returns the main content.
   * @return {ReactElement}
   */
  const getMainContent = () => (
    <>
      <H1>{category?.name}</H1>
      <P>{category?.description}</P>

      <CardContainer>
        {category?.children?.map((c: iCategory) => <CategoryCard key={c.slug} parentCategory={category} category={c} />)}
      </CardContainer>

      <CardContainer small={true}>
        {category?.product?.map((product: iSmallProduct) => <ProductCard key={product.slug} title={product.name} to={product.slug} summary={product.summary} />)}
      </CardContainer>
    </>

  );

  return (
    <Grid mainContent={getMainContent()}/>
  );
}
