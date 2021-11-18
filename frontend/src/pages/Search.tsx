import React, {SyntheticEvent, useState, ReactElement} from 'react';

import { Grid } from '../Components/Container/Grid';
import { ProductCard } from '../Components/Card/ProductCard';
import { Form } from '../Components/Form/Form';
import { H1 } from '../Components/Typography/H1';
import { P } from '../Components/Typography/P';
import { Divider } from '../Components/Divider/Divider';

import {search} from '../api/calls';

import { Filter } from '../Components/Filter/Filter'
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

  const getSearch = (): ReactElement => (
    <>
      <H1>Zoeken</H1>
      <P>Hier vind u hoe wonen, zorg, welzijn, werk en geldzaken in Den Haag geregeld zijn en wijzen we u de weg naar organisaties, activiteiten, hulp en initiatieven in uw eigen buurt.</P>
      <Form fields={getFields()} submitLabel='Zoeken' onSubmit={onSubmit}></Form>
    </>
  )

  const getMainContent = (): ReactElement => (
    <>
      <div className="card-list">
        {products.map((product) => <ProductCard key={product.slug} to={`/product/${product.slug}`} title={product.name} summary={product.summary} />)}
      </div>
    </>
  );

  const filterItems = [
    { id: 'test1', label: "test", value: "test", selected: true },
    { id: 'test2', label: "test2", value: "test", selected: false },
    { id: 'test3', label: "test3", value: "test", selected: false },
    { id: 'test4', label: "test4", value: "test", selected: false },
    { id: 'test5', label: "test5", value: "test", selected: false },
    { id: 'test6', label: "test6", value: "test", selected: false },
    { id: 'test7', label: "test7", value: "test", selected: false },
    { id: 'test8', label: "test9", value: "test", selected: false },
    { id: 'test9', label: "test8", value: "test", selected: false },
    { id: 'test10', label: "test10", value: "test", selected: false },
    { id: 'test11', label: "test11", value: "test", selected: false },
  ]

  const getSidebarContent = (): ReactElement => (
    <>
      <Filter items={filterItems} title="Filter op thema" />
      <Divider small={ true }></Divider>
      <Filter items={filterItems} title="Filter op tag" />
      <Divider small={ true }></Divider>
      <Filter items={filterItems} title="Filter op organisatie" />
    </>
  )

  return (
    <>
      <Grid mainContent={getSearch()} sidebarContent={<div></div> } />
      <Grid mainContent={getMainContent()} sidebarContent={getSidebarContent()} />
    </>
  );
}
