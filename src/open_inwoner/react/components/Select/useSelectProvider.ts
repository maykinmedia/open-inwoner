import { useSignal } from '@preact/signals';
import { useOnClickOutside } from '@react/lib/hooks/useOnClickOutside';
import { useContext } from 'preact/hooks';
import { useSelect } from '../Filters/hooks/useSelect';
import { SignalTestContext } from '../NewFilter/context';
import type { SelectContextValue } from './context';

export interface UseSelectProviderResult extends SelectContextValue {
  choices: { value: string; label: string }[];
  containerRef: ReturnType<typeof useSelect>['containerRef'];
  isOpen: boolean;
  activeIndex: number;
  handleKeyDown: (e: KeyboardEvent) => void;
  closeDropdown: () => void;
  toggleDropdown: () => void;
}

/**
 * Encapsulates all state and bridge logic for a Select group.
 *
 * - Reads from SignalTestContext when present (nested inside oip-sig-root-test).
 * - Falls back to own signal state when used standalone.
 * - Builds the choices array reactively as SelectOption children register.
 * - Returns the full SelectContextValue plus rendering helpers (keyboard nav,
 *   open/close) so Select.tsx only needs to provide context and render markup.
 */
export const useSelectProvider = (
  name: string,
  multiple: boolean
): UseSelectProviderResult => {
  const rootCtx = useContext(SignalTestContext);

  // Own state — used when no root context is present.
  const ownSelected = useSignal<string[]>([]);

  // Reactive choice registry — rebuilt as options self-register on mount.
  const choiceMap = useSignal<Record<string, string>>({});

  // Root context wins when present.
  const selectedValues: string[] = rootCtx
    ? (rootCtx.selected.value[name] ?? [])
    : ownSelected.value;

  const toggle = (value: string) => {
    if (rootCtx) {
      if (multiple) rootCtx.toggle(name, value);
      else rootCtx.toggleRadio(name, value);
      return;
    }
    if (multiple) {
      ownSelected.value = ownSelected.value.includes(value)
        ? ownSelected.value.filter((v) => v !== value)
        : [...ownSelected.value, value];
    } else {
      ownSelected.value = [value];
    }
  };

  const registerChoice = (
    value: string,
    optionLabel: string,
    initialSelected = false
  ) => {
    choiceMap.value = { ...choiceMap.value, [value]: optionLabel };
    if (rootCtx) {
      rootCtx.registerOption(name, value, optionLabel, initialSelected);
      return;
    }
    if (initialSelected) {
      ownSelected.value = [...ownSelected.value, value];
    }
  };

  const choices = Object.entries(choiceMap.value).map(([value, label]) => ({
    value,
    label,
  }));

  const {
    containerRef,
    isOpen,
    activeIndex,
    handleKeyDown,
    closeDropdown,
    toggleDropdown,
  } = useSelect({
    choices,
    multiple,
    name,
    toggleValue: (_name, value) => toggle(value),
    toggleValueRadio: (_name, value) => toggle(value),
  });

  return {
    name,
    multiple,
    selectedValues,
    registerChoice,
    toggle,
    choices,
    containerRef,
    isOpen,
    activeIndex,
    handleKeyDown,
    closeDropdown,
    toggleDropdown,
  };
};
