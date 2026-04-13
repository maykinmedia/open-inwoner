import { usePropsOrScriptData } from '@react/lib/json/json';
import { AnyComponent as AC } from 'preact';
import { FiltersProvider } from './context/FiltersContext';
import './Filters.scss';
import { IFiltersConfig, IFiltersProps } from '.';

const Filters: AC<IFiltersProps> = ({ data, dataId, children }, ctx) => {
  const config = usePropsOrScriptData<IFiltersConfig>(data, dataId);

  if (!config || !config.filterGroups.length) return <></>;

  return <FiltersProvider {...config}>{children}</FiltersProvider>;
};

export default Filters;
