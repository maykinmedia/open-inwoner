import { useSignal } from '@preact/signals';
import { useEffect, useRef } from 'preact/hooks';
import { useRequiredFormContext } from '../Form/FormContext';
import type { SelectContextValue } from './context';

export interface UseSelectProviderResult extends SelectContextValue {
  /** Current selected values — for the badge count in Select, not exposed via SelectContext. */
  selectedValues: string[];
  isOpen: boolean;
  containerRef: ReturnType<typeof useRef<HTMLElement>>;
  buttonRef: ReturnType<typeof useRef<HTMLButtonElement>>;
  toggleDropdown: () => void;
}

/**
 * Core logic for oip-select. Requires a parent oip-form (FormContext).
 * Throws if used outside oip-form.
 *
 * Value state lives entirely in FormContext. This hook only manages:
 *   - Option registration (label + default forwarded to FormContext)
 *   - Dropdown open/close state and keyboard focus
 */
export const useSelectProvider = (
  name: string,
  multiple: boolean,
  defaultValue?: string[]
): UseSelectProviderResult => {
  const formCtx = useRequiredFormContext();
  const binding = formCtx.register(name, defaultValue);
  const choiceMap = useSignal<Record<string, string>>({});
  const isOpen = useSignal(false);
  const containerRef = useRef<HTMLElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  const getHost = (): Element | null =>
    (containerRef.current?.getRootNode() as ShadowRoot)?.host ?? null;

  const getOptions = (): HTMLElement[] =>
    Array.from(
      getHost()?.querySelectorAll('oip-select-option') ?? []
    ) as HTMLElement[];

  const focusOption = (el: HTMLElement | undefined) =>
    el?.shadowRoot?.querySelector<HTMLElement>('.oip-filter__option')?.focus();

  const registerLabel = (value: string, label: string) => {
    if (choiceMap.value[value] === label) return;
    choiceMap.value = { ...choiceMap.value, [value]: label };
    formCtx.registerLabel(name, value, label);
  };

  const moveFocus = (direction: 'next' | 'prev') => {
    const options = getOptions();
    const focused = options.findIndex((el) => el.matches(':focus-within'));
    const next =
      direction === 'next'
        ? Math.min(focused + 1, options.length - 1)
        : Math.max(focused - 1, 0);
    focusOption(options[next]);
  };

  const close = () => {
    isOpen.value = false;
    requestAnimationFrame(() => buttonRef.current?.focus());
  };

  const open = () => {
    isOpen.value = true;
    requestAnimationFrame(() => focusOption(getOptions()[0]));
  };

  const toggleDropdown = () => (isOpen.value ? close() : open());

  const selectedValues = binding.value.value;

  // Sync to ElementInternals.setFormValue so a wrapping <form> captures values.
  useEffect(() => {
    const host = getHost() as any;
    if (!host?.internals_) return;
    if (selectedValues.length === 0) {
      host.internals_.setFormValue(null);
      return;
    }
    const fd = new FormData();
    selectedValues.forEach((v) => fd.append(name, v));
    host.internals_.setFormValue(fd);
  }, [selectedValues]);

  return {
    name,
    multiple,
    selectedValues,
    registerLabel,
    moveFocus,
    close,
    isOpen: isOpen.value,
    containerRef: containerRef as ReturnType<typeof useRef<HTMLElement>>,
    buttonRef: buttonRef as ReturnType<typeof useRef<HTMLButtonElement>>,
    toggleDropdown,
  };
};
