import { Filters, IFilterChoice } from '@react/components/Filters';
import { usePropsOrScriptData } from '@react/lib/json';
import { AnyComponent as AC } from 'preact';
import { useAfvalFilter } from '.';

/**
 * Type of the data.
 * The actual format is defined in the backend.
 */
export interface AfvalFilterConfig {
  addresses: string[];
  afval_types: IFilterChoice[];
  periode: number[];
}

/**
 * The names of the filters.
 * The name will be used in the GET query string.
 */
export type AfvalFilterTypes = 'periode' | 'adres' | 'afval-type';

/**
 * The AfvalFilter component props.
 * @param
 * @param
 */
export type IAfvalFilterProps = {
  /**
   * `dataId` is used by web-components.
   * Only works in combination with a json script.
   * The json script should contain data conform the `AfvalFilterConfig` type.
   */
  dataId?: string;
  /**
   * `data` is used by Preact components to pass data as an object.
   */
  data?: AfvalFilterConfig;
};

const AfvalFilter: AC<IAfvalFilterProps> = ({ data, dataId }) => {
  const config = usePropsOrScriptData<AfvalFilterConfig>(data, dataId);
  if (!config) return <></>;

  const afvalFilter = useAfvalFilter(config);
  if (!afvalFilter) return <></>;

  return <Filters data={afvalFilter} />;
};

export default AfvalFilter;
