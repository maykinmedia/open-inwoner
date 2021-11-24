export interface iTag {
  pk: Number,
  name: string,
}

export interface iProductLink {
  name: string,
  url: string,
}

export interface iImage {
  name: string,
  description: string,
  file: string,
  subjectLocation: any,
}

export interface iSmallProduct {
  url: string,
  name: string,
  slug: string,
  summary: string,
}

export interface iCategory {
  name: string,
  slug: string,
  description: string,
  icon: iImage,
  image: iImage,
  product?: iSmallProduct[],
  children?: iCategory[],
}


export interface iLocation {
  city: string,
  geometry: string,
  housenumber: string,
  name: string,
  postcode: string,
  street: string,
}


export interface iProduct {
  categories: iCategory[],
  content: string,
  costs: string,
  createdOn: string,
  files: any, // TODO
  link: string,
  links: iProductLink[],
  locations: iLocation[],
  name: string,
  organizations: string,
  relatedProducts: iProduct[],
  slug: string,
  summary: string,
  tags: iTag[],
}
