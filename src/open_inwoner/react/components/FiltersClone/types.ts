/**
 * The filter group frontend type.
 * @template T define which name the IFilterGroup can have.
 * @example IFilterGroup<"date" | "sort">
 */
export interface IFilterGroup<T extends string = string> {
  /**
   * Name of the filter group.
   * This is used to build the GET query string.
   */
  name: T;
  /**
   * Visible label used of the filter.
   */
  label: string;
  /**
   * Array of choices used to render the filter options.
   */
  choices: IFilterChoice[];
  /**
   * Render the filter options as radio's (false) or checkboxes (true)
   * @default true // renders with checkboxes
   */
  multiple?: boolean;
}

/**
 * Interface for the filter choice.
 * Used in the filter options.
 */
export interface IFilterChoice {
  label: string;
  value: string;
}

/**
 * The initial/current state of the filters
 * @template T define which names the FilterState have.
 * @example
 * ```
 * const filterState: FilterState<"date", "sort"> = {
 *   date: ['2024']
 *   sort: []
 * }
 * ```
 */
export type FilterState<T extends string = string> = Record<T, string[]>;

/**
 * The config for the filters.
 * This config is used to build the actual filters.
 */
export interface IFiltersConfig<T extends string = string> {
  filterGroups: IFilterGroup<T>[];
  initialFilterState: FilterState<T>;
}

/**
 * Type of component props the filters component.
 */
export interface IFiltersProps {
  /**
   * `dataId` is used by web-components.
   * Only works in combination with a json script.
   * The json script should contain data conform the `IFiltersConfig` type.
   */
  dataId?: string;
  /**
   * `data` is used by Preact components to pass data as an object.
   */
  data?: IFiltersConfig;
}
