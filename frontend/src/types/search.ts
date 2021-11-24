export interface iBucket {
  slug: string,
  name: string,
  count: number,
  selected: false,
}

export interface iFacet {
  name: string,
  buckets: Array<iBucket>,
}

export interface iSearchResult {
  name: string,
  slug: string,
  summary: string,
  content: string,
}

export interface iSearchResults {
  count: number,
  next: string | null,
  previous: string | null,
  results: Array<iSearchResult>,
  facets: Array<iFacet>,
}
