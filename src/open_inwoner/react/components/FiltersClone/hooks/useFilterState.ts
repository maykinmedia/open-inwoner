import { useComputed, useSignal } from '@preact/signals';
import isEqual from 'lodash/isEqual';
import mapValues from 'lodash/mapValues';
import xor from 'lodash/xor';
import { FilterState } from '..';

export const useFilterState = (initialFilterState: FilterState) => {
  const selectedFilters = useSignal<FilterState>(initialFilterState);

  const toggleValue = (groupName: string, value: string) => {
    const groupValue = selectedFilters.value[groupName] || [];
    selectedFilters.value = {
      ...selectedFilters.value,
      [groupName]: xor(groupValue, [value]),
    };
  };

  const toggleValueRadio = (groupName: string, value: string) => {
    selectedFilters.value = {
      ...selectedFilters.value,
      [groupName]: [value],
    };
  };

  const clearAllFilters = () => {
    selectedFilters.value = mapValues(selectedFilters.value, () => []);
  };

  const isDirty = useComputed(
    () => !isEqual(initialFilterState, selectedFilters.value)
  );

  return {
    selectedFilters,
    isDirty,
    toggleValue,
    toggleValueRadio,
    clearAllFilters,
  };
};
