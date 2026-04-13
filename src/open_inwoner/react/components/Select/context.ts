import { createContext } from 'preact';
import { useContext } from 'preact/hooks';

export interface SelectContextValue {
  /** The filter group name this Select manages. */
  name: string;
  /** Whether this group uses checkboxes (true) or radio buttons (false). */
  multiple: boolean;
  /** Currently selected values for this group. */
  selectedValues: string[];
  /**
   * Called by Option on mount to register its value/label.
   * Also propagates up to the root SignalTestContext when present.
   */
  registerChoice: (
    value: string,
    label: string,
    initialSelected?: boolean
  ) => void;
  /** Toggle a value in this group (respects multiple). */
  toggle: (value: string) => void;
}

export const SelectContext = createContext<SelectContextValue | null>(null);

export const useSelectContext = (): SelectContextValue => {
  const ctx = useContext(SelectContext);
  if (!ctx)
    throw new Error('useSelectContext must be used within a Select component');
  return ctx;
};
