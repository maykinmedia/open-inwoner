import { type ReadonlySignal, type Signal } from '@preact/signals';
import { createContext } from 'preact';
import { useContext } from 'preact/hooks';

export interface ItemGroup {
  name: string;
  items: string[];
}

export interface SignalTestContextValue {
  /** Static config — which groups exist */
  groups: ItemGroup[];
  /** Mutable selection state */
  selected: Signal<Record<string, string[]>>;
  /** Computed — true when anything is selected */
  isAnySelected: ReadonlySignal<boolean>;
  /** Toggle a single item in a group */
  toggle: (group: string, item: string) => void;
  /** Clear all selections */
  clear: () => void;
}

export const SignalTestContext = createContext<SignalTestContextValue | null>(
  null
);

export const useSignalTest = (): SignalTestContextValue => {
  const ctx = useContext(SignalTestContext);
  if (!ctx) throw new Error('useSignalTest must be used within oip-sig-root');
  return ctx;
};
