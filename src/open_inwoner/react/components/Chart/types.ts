export interface AfvalLediging {
  tijdstip_dag?: string;
  tijdstip_datum: string;
  tijdstip_tijd?: string;
  gewicht: string;
  kosten?: string;
}

export interface AfvalContainer {
  identifier: string;
  type: string;
  totaal_gewicht: string;
  ledigingen: AfvalLediging[];
}

export interface AfvalObject {
  object_id: string;
  object_address: string;
  totaal_gewicht: string;
  containers: AfvalContainer[];
}

export type AfvalData = AfvalObject[];

export type ChartPeriod = 'week' | 'month' | 'year';

export interface ChartDataPoint {
  x: string;
  y: number | null;
}

/** Cumulative trend line series, keyed by the unit they track. */
export interface Trends {
  weight: ChartDataPoint[];
  cost: ChartDataPoint[];
}

/** Localized legend labels for the trend lines in {@link Trends}. */
export type TrendLabels = Record<keyof Trends, string>;

export interface ContainerSeries {
  type: string;
  address: string;
  containerIndex: number;
  points: ChartDataPoint[];
}
