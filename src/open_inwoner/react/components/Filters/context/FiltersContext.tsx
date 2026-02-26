import { serializeParams } from '@react/lib/url/url';
import some from 'lodash/some';
import { type AnyComponent as AC, createContext } from 'preact';
import { useCallback, useContext, useMemo } from 'preact/hooks';
import { type IFilterGroup, type IFiltersConfig, useFilterState } from '..';

export interface FiltersContextValue {
  // State
  filterGroups: IFilterGroup[];
  selectedFilters: Record<string, string[]>;
  isDirty: boolean;

  // Computed
  isFiltered: boolean;

  // Actions
  toggleValue: (groupName: string, value: string) => void;
  toggleValueRadio: (groupName: string, value: string) => void;
  clearAllFilters: () => void;
  applyFilters: () => void;
}

const FiltersContext = createContext<FiltersContextValue | null>(null);

/**
 * Provider provides all business logic for the filter.
 * Now we do not have to pass all filter methods down to all sub-components.
 */
export const FiltersProvider: AC<IFiltersConfig> = ({
  initialFilterState = {},
  filterGroups = [],
  children,
}) => {
  const {
    // Current state
    selectedFilters,
    isDirty,
    // Selected filters control.
    toggleValue,
    toggleValueRadio,
    clearAllFilters,
  } = useFilterState(initialFilterState);

  // Apply filters (navigates to URL with query params)
  const applyFilters = useCallback(() => {
    const baseUrl = location.origin + location.pathname;
    const params = serializeParams(selectedFilters);
    const queryString = params.toString();
    const targetUrl = queryString ? `${baseUrl}?${queryString}` : baseUrl;
    window.location.assign(targetUrl);
  }, [selectedFilters]);

  // Computed values
  const isFiltered = useMemo(
    () => some(selectedFilters, (values) => values.length > 0),
    [selectedFilters]
  );

  const value: FiltersContextValue = useMemo(
    () => ({
      filterGroups,
      selectedFilters,
      isFiltered,
      isDirty,
      toggleValue,
      toggleValueRadio,
      clearAllFilters,
      applyFilters,
    }),
    [
      filterGroups,
      selectedFilters,
      isFiltered,
      isDirty,
      toggleValue,
      toggleValueRadio,
      clearAllFilters,
      applyFilters,
    ]
  );

  return (
    <div className="oip-filter__wrapper">
      <FiltersContext.Provider value={value}>
        {children}
      </FiltersContext.Provider>
    </div>
  );
};

/**
 * Hook to access filter context
 * Throws error if used outside FilterProvider
 */
export const useFilterContext = (): FiltersContextValue => {
  const context = useContext(FiltersContext);

  if (!context) {
    throw new Error(
      'useFilterContext must be used within a FilterProvider. ' +
        'Wrap your component tree with <FilterProvider>.'
    );
  }

  return context;
};
