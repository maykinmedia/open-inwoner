import { useComputed, useSignal } from '@preact/signals';
import isEqual from 'lodash/isEqual';
import mapValues from 'lodash/mapValues';
import xor from 'lodash/xor';
import { type AnyComponent as AC } from 'preact';
import { useRef } from 'preact/hooks';
import { SignalTestContext } from './context';

/**
 * oip-filter-root
 * Creates shared signal state and provides it via context.
 * Groups and their labels are registered lazily by oip-filter-option children on mount.
 */
const Root: AC<{}> = ({ children }) => {
  const selected = useSignal<Record<string, string[]>>({});

  // Captured once as each option registers — used to compute isDirty.
  const initial = useRef<Record<string, string[]>>({});

  // Stable map of group → value → display label, populated on option mount.
  const optionLabels = useRef<Record<string, Record<string, string>>>({});

  const isDirty = useComputed(() => !isEqual(selected.value, initial.current));

  const isFiltered = useComputed(() =>
    Object.values(selected.value).some((v) => v.length > 0)
  );

  const registerOption = (
    group: string,
    value: string,
    label: string,
    initialSelected: boolean
  ) => {
    // Store display label
    if (!optionLabels.current[group]) optionLabels.current[group] = {};
    optionLabels.current[group][value] = label;

    // Initialize group in both maps if first option in that group
    if (!(group in initial.current)) {
      initial.current[group] = [];
      selected.value = { ...selected.value, [group]: [] };
    }

    if (initialSelected) {
      if (!initial.current[group].includes(value)) {
        initial.current[group] = [...initial.current[group], value];
      }
      if (!selected.value[group].includes(value)) {
        selected.value = {
          ...selected.value,
          [group]: [...selected.value[group], value],
        };
      }
    }
  };

  const toggle = (group: string, value: string) => {
    const current = selected.value[group] ?? [];
    selected.value = { ...selected.value, [group]: xor(current, [value]) };
  };

  const toggleRadio = (group: string, value: string) => {
    selected.value = { ...selected.value, [group]: [value] };
  };

  const clearAll = () => {
    selected.value = mapValues(selected.value, () => []);
  };

  const applyFilters = () => {
    const params = new URLSearchParams();
    Object.entries(selected.value).forEach(([group, values]) => {
      values.forEach((v) => params.append(group, v));
    });
    const qs = params.toString();
    window.location.assign(
      qs
        ? `${location.origin}${location.pathname}?${qs}`
        : `${location.origin}${location.pathname}`
    );
  };

  return (
    <SignalTestContext.Provider
      value={{
        selected,
        isDirty,
        isFiltered,
        optionLabels: optionLabels.current,
        registerOption,
        toggle,
        toggleRadio,
        clearAll,
        applyFilters,
      }}
    >
      {children}
    </SignalTestContext.Provider>
  );
};

export default Root;
