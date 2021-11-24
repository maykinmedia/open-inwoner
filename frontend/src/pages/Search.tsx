import React, {SyntheticEvent, ChangeEvent, useState, ReactElement, useEffect} from 'react';

import { Grid } from '../Components/Container/Grid';
import { LinkList } from '../Components/LinkList/LinkList';
import { Form } from '../Components/Form/Form';
import { H1 } from '../Components/Typography/H1';
import { P } from '../Components/Typography/P';
import { Divider } from '../Components/Divider/Divider';
import { Button } from '../Components/Button/Button';
import { ButtonRow } from '../Components/Button/ButtonRow';
import { Pagination } from '../Components/Pagination/Pagination';

import {search} from '../api/calls';

import { Filter } from '../Components/Filter/Filter'
import {iField} from '../types/field';
import { iFacet, iSearchResult } from '../types/search';

interface iFilters {
  categories?: Array<string>,
  tags?: Array<string>,
  organizations?: Array<string>,
}

export default function Search() {
  const [searchResults, setSearchResults] = useState<iSearchResult[]>([]);
  const [page, setPage] = useState<number>(1);
  const [resultCount, setResultCount] = useState<number>(0);
  const [facets, setFacets] = useState<iFacet[]>([]);
  const [searchTerms, setSearchTerms] = useState<Array<string>>([]);
  const [filters, setFilters] = useState<iFilters>({
    categories: [],
    tags: [],
    organizations: [],
  });

  useEffect(() => {
    const load = async () => {
      await onSubmit(null, {query: searchTerms.join(" ")})
    };
    load();
  }, [filters, page]);

  const onSubmit = async (event: SyntheticEvent | null, data: { query: string }): Promise<void> => {
    const {query} = data;

    event?.preventDefault();
    const localSearchResults = await search(page, filters, query);
    if (true) {
      setSearchResults(localSearchResults.results);
      setResultCount(localSearchResults.count);
    } else {
      setResultCount(0);
      setSearchResults([]);
    }
    setFacets(localSearchResults.facets);
  };

  const searchChange = (event:ChangeEvent) => {
    setSearchTerms(event.currentTarget.value.split(" "));
  }

  const removeSearchTerm = async (event:SyntheticEvent) => {
    const index = event.currentTarget.dataset.index;
    let localSearchTerms = [...searchTerms]
    localSearchTerms.splice(index, 1);
    setSearchTerms(localSearchTerms);
    await onSubmit(null, {query: searchTerms.join(" ")})
  }

  const toggleFilter = async (event: SyntheticEvent) => {
    const slug = event.currentTarget.id;
    const facetName: string = event.currentTarget.name;
    const checked = event.currentTarget.checked;

    const removeValue = async (list: Array<string>, value: string) => {
      const index = list.indexOf(value);
      if (index != null && index > -1) {
        list.splice(index, 1);
      }
    }

    let localFilters: iFilters = {
      categories: [],
      tags: [],
      organizations: [],
    }
    Object.assign(localFilters, filters);

    if (facetName === "categories") {
      if (checked) {
        localFilters.categories?.push(slug);
      } else {
        await removeValue(localFilters.categories, slug);
      }
    }
    if (facetName === "tags") {
      if (checked) {
        localFilters.tags?.push(slug);
      } else {
        await removeValue(localFilters.tags, slug);
      }
    }
    if (facetName === "organizations") {
      if (checked) {
        localFilters.organizations?.push(slug);
      } else {
        await removeValue(localFilters.organizations, slug);
      }
    }
    await setFilters(localFilters);
    // await onSubmit(null, {query: searchTerms.join(" ")})
  }

  const changePage = async (event: SyntheticEvent) => {
    setPage(event.currentTarget.dataset.page);
  }

  const prevPage = async (event: SyntheticEvent) => {
    setPage(page - 1);
  }

  const nextPage = async (event: SyntheticEvent) => {
    setPage(page + 1);
  }

  const getFields = (): iField[] => [
    {
      label: 'Zoek op trefwoord', name: 'query', type: 'text', value: searchTerms.join(" "), onChange: searchChange, required: false
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
    let links = searchResults.map((searchResult) => {
      return {
        name: searchResult.name,
        intro: searchResult.summary,
        href: `/products/${searchResult.slug}`,
        type: "product"
      }
    });
    return <LinkList links={links} count={resultCount} />
  }

  const getMainContent = (): ReactElement => (
    <>
      {displayResults()}
      <Pagination prevAction={prevPage} nextAction={nextPage} defaultAction={changePage} currentPage={page} itemsPerPage={10} totalItems={100} />
    </>
  );

  const getSidebarContent = (): ReactElement => (
    <>
      {facets?.map((facet, index) => {
        return (
          <div key={ index }>
            <Filter items={facet.buckets} facet={facet} action={toggleFilter} />
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
