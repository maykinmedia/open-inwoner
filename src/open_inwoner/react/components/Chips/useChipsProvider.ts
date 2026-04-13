import { useComputed, useSignal } from '@preact/signals';
import mapValues from 'lodash/mapValues';
import xor from 'lodash/xor';
import { useContext } from 'preact/hooks';
import { SignalTestContext } from '../NewFilter/context';
import type { ChipsContextValue } from './context';

/**
 * Encapsulates all state and bridge logic for Chips.
 *
 * - Reads from SignalTestContext when present (nested inside oip-sig-root-test).
 * - Falls back to own signal state when used standalone.
 * - Returns the full ChipsContextValue so Chips.tsx only needs to provide
 *   context and render markup.
 */
export const useChipsProvider = (): ChipsContextValue => {
  const rootCtx = useContext(SignalTestContext);

  // Own state — used when no root context is present.
  const ownSelected = useSignal<Record<string, string[]>>({});

  const selected = rootCtx?.selected ?? ownSelected;

  const isFiltered = useComputed(() =>
    Object.values(selected.value).some((v) => v.length > 0)
  );

  const toggle = (group: string, value: string) => {
    if (rootCtx) {
      rootCtx.toggle(group, value);
      return;
    }
    const current = ownSelected.value[group] ?? [];
    ownSelected.value = {
      ...ownSelected.value,
      [group]: xor(current, [value]),
    };
  };

  const clearAll = () => {
    if (rootCtx) {
      rootCtx.clearAll();
      return;
    }
    ownSelected.value = mapValues(ownSelected.value, () => []);
  };

  return {
    selected,
    isFiltered,
    optionLabels: rootCtx?.optionLabels ?? {},
    toggle,
    clearAll,
  };
};
