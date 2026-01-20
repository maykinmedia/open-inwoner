/**
 * Base card properties shared across all card types
 */
export interface DefaultCard {
  title: string;
  identificatie: string;
  detailUrl: string;
  renderAsHeading?: boolean | string;
}

/**
 * Card showing a Theme with title and description
 */
export type ThemeCardOptions = DefaultCard & {
  description?: string;
  createdDate?: string;
  updatedDate?: string;
  date?: undefined;
  address?: undefined;
  keywords?: undefined;
  code?: undefined;
  gepubliceerd?: undefined;
  publicatieStartDatum?: undefined;
  toegestaneStatussen?: undefined;
  prijs?: undefined;
};

/**
 * Card showing a Product with title and description
 */
export type ProductCardOptions = DefaultCard & {
  description?: string;
  createdDate?: string;
  updatedDate?: string;
  date?: undefined;
  address?: undefined;
  keywords?: undefined;
  code?: undefined;
  gepubliceerd?: undefined;
  publicatieStartDatum?: undefined;
  toegestaneStatussen?: undefined;
  prijs?: string | number;
};

/**
 * Card showing a ProductType with code and keywords
 */
export type ProductTypeCardOptions = DefaultCard & {
  description?: undefined;
  createdDate?: string;
  updatedDate?: string;
  date?: undefined;
  address?: undefined;
  keywords?: string[] | string;
  code: string;
  gepubliceerd?: boolean | string;
  publicatieStartDatum?: string;
  toegestaneStatussen?: string[] | string;
  prijs?: undefined;
};

/**
 * Card showing a Zaak with title and optional description
 */
export type ZaakCardOptions = DefaultCard & {
  description?: string;
  createdDate?: undefined;
  updatedDate?: undefined;
  date?: undefined;
  address?: undefined;
  keywords?: undefined;
  code?: undefined;
  gepubliceerd?: undefined;
  publicatieStartDatum?: undefined;
  toegestaneStatussen?: undefined;
  prijs?: undefined;
};

/**
 * Card showing an Appointment with date and address
 */
export type AppointmentCardOptions = DefaultCard & {
  date: string;
  address: string;
  description?: undefined;
  createdDate?: undefined;
  updatedDate?: undefined;
  keywords?: undefined;
  code?: undefined;
  gepubliceerd?: undefined;
  publicatieStartDatum?: undefined;
  toegestaneStatussen?: undefined;
  prijs?: undefined;
};

/**
 * Card showing a Samenwerking with description
 */
export type SamenwerkingCardOptions = DefaultCard & {
  description: string;
  createdDate?: undefined;
  updatedDate?: undefined;
  date?: undefined;
  address?: undefined;
  keywords?: undefined;
  code?: undefined;
  gepubliceerd?: undefined;
  publicatieStartDatum?: undefined;
  toegestaneStatussen?: undefined;
  prijs?: undefined;
};

/**
 * Union of all valid card type combinations
 */
export type CardTileTypes =
  | ThemeCardOptions
  | ProductCardOptions
  | ProductTypeCardOptions
  | ZaakCardOptions
  | AppointmentCardOptions
  | SamenwerkingCardOptions;
