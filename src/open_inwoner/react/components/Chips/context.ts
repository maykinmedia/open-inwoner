import type { ReadonlySignal, Signal } from '@preact/signals';
import { createContext } from 'preact';
import { useContext } from 'preact/hooks';

export interface ChipsContextValue {
  /** All currently selected values, keyed by group name. */
  selected: Signal<Record<string, string[]>>;
  /** True when at least one filter is active. */
  isFiltered: ReadonlySignal<boolean>;
  /** Stable map of group → value → display label, built as options register. */
  optionLabels: Record<string, Record<string, string>>;
  /** Toggle a single value within a group. */
  toggle: (group: string, value: string) => void;
  /** Clear all selected values. */
  clearAll: () => void;
}

export const ChipsContext = createContext<ChipsContextValue | null>(null);

export const useChipsContext = (): ChipsContextValue => {
  const ctx = useContext(ChipsContext);
  if (!ctx)
    throw new Error('useChipsContext must be used within a Chips component');
  return ctx;
};
