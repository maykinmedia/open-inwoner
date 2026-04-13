import { type ReadonlySignal, type Signal } from '@preact/signals';
import { createContext } from 'preact';
import { useContext } from 'preact/hooks';

export interface SignalTestContextValue {
  /** Mutable selection state — keyed by group name */
  selected: Signal<Record<string, string[]>>;
  /** True when current selection differs from initial (page-load) state */
  isDirty: ReadonlySignal<boolean>;
  /** True when at least one filter is selected */
  isFiltered: ReadonlySignal<boolean>;
  /** Stable map of group → value → display label, built by oip-filter-option on mount */
  optionLabels: Record<string, Record<string, string>>;
  /** Called by oip-filter-option on mount to register itself */
  registerOption: (
    group: string,
    value: string,
    label: string,
    initialSelected: boolean
  ) => void;
  /** Toggle a value in a multi-select group */
  toggle: (group: string, value: string) => void;
  /** Replace selection in a single-select group */
  toggleRadio: (group: string, value: string) => void;
  /** Reset all groups to empty */
  clearAll: () => void;
  /** Serialize selected state to URL query params and navigate */
  applyFilters: () => void;
}

export const SignalTestContext = createContext<SignalTestContextValue | null>(
  null
);

export const useSignalTest = (): SignalTestContextValue => {
  const ctx = useContext(SignalTestContext);
  if (!ctx)
    throw new Error('useSignalTest must be used within oip-filter-root');
  return ctx;
};
