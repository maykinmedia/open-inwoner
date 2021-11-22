import React, {SyntheticEvent, useState, ReactElement} from 'react';

import { Grid } from '../Components/Container/Grid';
import { LinkList } from '../Components/LinkList/LinkList';
import { Form } from '../Components/Form/Form';
import { H1 } from '../Components/Typography/H1';
import { P } from '../Components/Typography/P';
import { Divider } from '../Components/Divider/Divider';
import { Button } from '../Components/Button/Button';
import { ButtonRow } from '../Components/Button/ButtonRow';

import {search} from '../api/calls';

import { Filter } from '../Components/Filter/Filter'
import {iField} from '../types/field';
import { iProduct } from '../types/pdc';

export default function Search() {
  const [products, setProducts] = useState<iProduct[]>([]);
  const [searchTerms, setSearchTerms] = useState<Array<string>>([]);
  // const [filters, setFilters] = useState<any>([]);

  const onSubmit = async (event: SyntheticEvent, data: { query: string }): Promise<void> => {
    const {query} = data;

    event.preventDefault();
    const returnedProducts = await search(query);
    setProducts(returnedProducts)
  };

  const searchChange = (event:SyntheticEvent) => {
    setSearchTerms(event.currentTarget.value.split(" "));
  }

  const removeSearchTerm = async (event:SyntheticEvent) => {
    const index = event.currentTarget.dataset.index;
    let localSearchTerms = [...searchTerms]
    localSearchTerms.splice(index, 1);
    setSearchTerms(localSearchTerms);
  }

  const getFields = (): iField[] => [
    {
      label: 'Zoek op trefwoord', name: 'query', type: 'text', value: searchTerms.join(" "), onChange: searchChange
    },
  ];

  const getButtons = () => {
    if (searchTerms) {
      return searchTerms.map((searchTerm, index) => {
        if (searchTerm) {
          return <Button key={index} iconPosition="after" bordered={true} closeAction={removeSearchTerm} data-index={index}>{searchTerm}</Button>
        }
        return null;
      })
    }
  }

  const getSearch = (): ReactElement => (
    <>
      <H1>Zoeken</H1>
      <P>Hier vind u hoe wonen, zorg, welzijn, werk en geldzaken in Den Haag geregeld zijn en wijzen we u de weg naar organisaties, activiteiten, hulp en initiatieven in uw eigen buurt.</P>
      <Form fields={getFields()} submitLabel='Zoeken' onSubmit={onSubmit}></Form>
      {searchTerms.length > 0 && <ButtonRow startingText="U zocht op:" buttons={getButtons()} />}
    </>
  )

  const displayResults = () => {
    let links = products.map((product) => {
      return {
        name: product.name,
        href: `/products/${product.slug}`,
        type: "product"
      }
    });
    return <LinkList links={links} />
  }

  const getMainContent = (): ReactElement => (
    <>
      {displayResults()}
    </>
  );

  const filterItems = [
    { slug: 'test1', name: "test", count: 0, selected: true },
    { slug: 'test2', name: "test2", count: 0, selected: false },
    { slug: 'test3', name: "test3", count: 0, selected: false },
    { slug: 'test4', name: "test4", count: 0, selected: false },
    { slug: 'test5', name: "test5", count: 0, selected: false },
    { slug: 'test6', name: "test6", count: 0, selected: false },
    { slug: 'test7', name: "test7", count: 0, selected: false },
    { slug: 'test8', name: "test9", count: 0, selected: false },
    { slug: 'test9', name: "test8", count: 0, selected: false },
    { slug: 'test10', name: "test10", count: 0, selected: false },
    { slug: 'test11', name: "test11", count: 0, selected: false },
  ]

  const facets = [{
    name: "Filter op thema",
    buckets: filterItems,
  }, {
    name: "Filter op tag",
    buckets: filterItems,
  }, {
    name: "Filter op organisatie",
    buckets: filterItems,
  }];

  const getSidebarContent = (): ReactElement => (
    <>
      {facets?.map((facet, index) => {
        return (
          <div key={ index }>
            <Filter items={facet.buckets} title={ facet.name } />
            <Divider small={ true }></Divider>
          </div>
        )
      })}
    </>
  )

  return (
    <>
      <Grid mainContent={getSearch()} sidebarContent={<div></div> } />
      <Grid mainContent={getMainContent()} sidebarContent={getSidebarContent()} />
    </>
  );
}
