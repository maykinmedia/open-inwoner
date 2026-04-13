import { useComputed } from '@preact/signals';
import type { ReadonlySignal, Signal } from '@preact/signals';
import { serializeParams } from '@react/lib/url/url';
import some from 'lodash/some';
import {
  type AnyComponent as AC,
  ComponentChildren,
  createContext,
} from 'preact';
import { useContext } from 'preact/hooks';
import {
  type FilterState,
  type IFilterGroup,
  type IFiltersConfig,
  useFilterState,
} from '..';

export interface FiltersContextValue {
  // State
  filterGroups: IFilterGroup[];
  selectedFilters: Signal<FilterState>;
  isDirty: ReadonlySignal<boolean>;
  isFiltered: ReadonlySignal<boolean>;

  // Actions
  toggleValue: (groupName: string, value: string) => void;
  toggleValueRadio: (groupName: string, value: string) => void;
  clearAllFilters: () => void;
  applyFilters: () => void;
}

const FiltersContext = createContext<FiltersContextValue | null>(null);

/**
 * Provider provides all business logic for the filter.
 * State is stored in signals so updates propagate across shadow DOM boundaries.
 */
export const FiltersProvider: AC<
  IFiltersConfig & { children?: ComponentChildren }
> = ({ initialFilterState = {}, filterGroups = [], children }) => {
  const {
    selectedFilters,
    isDirty,
    toggleValue,
    toggleValueRadio,
    clearAllFilters,
  } = useFilterState(initialFilterState);

  const isFiltered = useComputed(() =>
    some(selectedFilters.value, (values) => values.length > 0)
  );

  const applyFilters = () => {
    const baseUrl = location.origin + location.pathname;
    const params = serializeParams(selectedFilters.value);
    const queryString = params.toString();
    const targetUrl = queryString ? `${baseUrl}?${queryString}` : baseUrl;
    window.location.assign(targetUrl);
  };

  const value: FiltersContextValue = {
    filterGroups,
    selectedFilters,
    isFiltered,
    isDirty,
    toggleValue,
    toggleValueRadio,
    clearAllFilters,
    applyFilters,
  };

  return (
    <div className="oip-filter__wrapper">
      <FiltersContext.Provider value={value}>
        {children}
      </FiltersContext.Provider>
    </div>
  );
};

/**
 * Hook to access filter context.
 * Throws if used outside FiltersProvider.
 */
export const useFilterContext = (): FiltersContextValue => {
  const context = useContext(FiltersContext);
  if (!context) {
    throw new Error(
      'useFilterContext must be used within a FiltersProvider. ' +
        'Wrap your component tree with <FiltersProvider>.'
    );
  }
  return context;
};
