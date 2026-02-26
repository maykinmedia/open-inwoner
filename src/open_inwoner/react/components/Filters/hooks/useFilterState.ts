import isEqual from 'lodash/isEqual';
import mapValues from 'lodash/mapValues';
import xor from 'lodash/xor';
import { useCallback, useMemo, useState } from 'preact/hooks';
import { FilterState } from '..';

export const useFilterState = (initialFilterState: FilterState) => {
  const [selectedFilters, setSelectedFilters] =
    useState<FilterState>(initialFilterState);

  // Toggle a single value (multiple: checkbox)
  const toggleValue = useCallback((groupName: string, value: string) => {
    setSelectedFilters((prev) => {
      const groupValue = prev[groupName] || [];
      return {
        ...prev,
        [groupName]: xor(groupValue, [value]),
      };
    });
  }, []);

  // Toggle a single value (single: radio)
  const toggleValueRadio = useCallback((groupName: string, value: string) => {
    setSelectedFilters((prev) => {
      return {
        ...prev,
        [groupName]: [value],
      };
    });
  }, []);

  // Clear all filters
  const clearAllFilters = useCallback(() => {
    setSelectedFilters((prev) => mapValues(prev, () => []));
  }, []);

  // True when values have changed since last GET.
  const isDirty = useMemo(() => {
    return !isEqual(initialFilterState, selectedFilters);
  }, [initialFilterState, selectedFilters]);

  return {
    // Current state
    selectedFilters,
    isDirty,
    // Selected filters control.
    toggleValue,
    toggleValueRadio,
    clearAllFilters,
  };
};
