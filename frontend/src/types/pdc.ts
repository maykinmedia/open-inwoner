export interface iProduct {
    name: string,
    slug: string,
    summary: string,
    link: string,
    content: string,
    categories: Array<iCategory>,
    relatedProducts: Array<iProduct>,
    tags: Array<iTag>,
    costs: string,
    created_on: string,
    organizations: string,
    links: Array<iProductLink>,
}

export interface iSmallProduct {
    url: string,
    name: string,
    slug: string,
    summary: string,
}

export interface iProductLink {
    name: string,
    url: string,
}

export interface iCategory {
    name: string,
    slug: string,
    description: string,
    icon: iImage,
    image: iImage,
    product?: Array<iSmallProduct>,
    children?: Array<iCategory>,
}

export interface iTag {
    pk: Number,
    name: string,
}

export interface iImage {
    name: string,
    description: string,
    file: string,
    subject_location: any,
}
