import React, {SyntheticEvent, useState} from 'react';

import { Grid } from '../Components/Container/Grid';
import { ProductCard } from '../Components/Card/ProductCard';
import { Form } from '../Components/Form/Form';
import { H1 } from '../Components/Typography/H1';
import {P} from '../Components/Typography/P';

import {search} from '../api/calls';

import {iField} from '../types/field';
import { iProduct } from '../types/pdc';

export default function Search() {
  const [products, setProducts] = useState<iProduct[]>([]);

  const onSubmit = async (event: SyntheticEvent, data: { query: string }): Promise<void> => {
    const {query} = data;

    event.preventDefault();
    const returnedProducts = await search(query);
    setProducts(returnedProducts)
  };

  const getFields = (): iField[] => [
    {label: 'Zoek op trefwoord', name: 'query', type: 'text'},
  ];

  const getRight = () => (
    <>
      <H1>Zoeken</H1>
      <P>Hier vind u hoe wonen, zorg, welzijn, werk en geldzaken in Den Haag geregeld zijn en wijzen we u de weg naar organisaties, activiteiten, hulp en initiatieven in uw eigen buurt.</P>
      <Form fields={getFields()} submitLabel='Zoeken' onSubmit={onSubmit}></Form>
      <div className="card-list">
          {products.map((product) => <ProductCard key={product.slug} to={`/product/${product.slug}`} title={product.name} summary={product.summary} />)}
        </div>
    </>
  );

  return (
    <Grid isLoggedIn mainContent={getRight()} />
  );
}
