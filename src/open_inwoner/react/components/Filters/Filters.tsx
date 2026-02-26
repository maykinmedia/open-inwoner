import { usePropsOrScriptData } from '@react/lib/json/json';
import { AnyComponent as AC } from 'preact';
import Filter from './components/Filter/Filter';
import FilterBar from './components/FilterBar/FilterBar';
import FilterChips from './components/FilterChips/FilterChips';
import { FiltersProvider } from './context/FiltersContext';
import './Filters.scss';
import { IFiltersConfig, IFiltersProps } from '.';

const Filters: AC<IFiltersProps> = ({ data, dataId, showChips = true }) => {
  const config = usePropsOrScriptData<IFiltersConfig>(data, dataId);

  // Fail silently
  if (!config || !config.filterGroups.length) return <></>;

  return (
    <FiltersProvider {...config}>
      <FilterBar>
        {config.filterGroups.map((group) => {
          if (!group.choices.length) return;
          return (
            <Filter
              key={group.name}
              name={group.name}
              label={group.label}
              choices={group.choices}
              multiple={group.multiple}
            />
          );
        })}
      </FilterBar>
      {showChips && <FilterChips />}
    </FiltersProvider>
  );
};

export default Filters;
