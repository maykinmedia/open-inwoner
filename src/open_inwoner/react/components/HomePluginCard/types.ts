/**
 * Base card properties shared across all card types on Home page
 */
export interface DefaultCard {
  title: string;
  identificatie: string;
  detailUrl: string;
  renderAsHeading?: boolean | string;
}

/**
 * Card showing a zaak with title
 */
export type ZaakCardOptions = DefaultCard & {
  description?: string;
  date?: undefined;
  address?: undefined;
};

/**
 * Card showing an Balie-afspraak with date and address
 */
export type AppointmentCardOptions = DefaultCard & {
  date: string;
  address: string;
  description?: undefined;
};

/**
 * Card showing a samenwerking with description
 */
export type SamenwerkingCardOptions = DefaultCard & {
  description: string;
  date?: undefined;
  address?: undefined;
};

/**
 * Union of all valid card type combinations
 */
export type HomepageCardTypes =
  ZaakCardOptions | AppointmentCardOptions | SamenwerkingCardOptions;
