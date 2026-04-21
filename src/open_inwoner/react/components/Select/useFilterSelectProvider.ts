import { useSignal } from '@preact/signals';
import { useContext, useEffect, useRef } from 'preact/hooks';
import { SignalTestContext } from '../NewFilter/context';
import type { SelectContextValue } from './context';
import type { UseSelectProviderResult } from './useSelectProvider';

export const useFilterSelectProvider = (
  name: string,
  multiple: boolean
): UseSelectProviderResult => {
  const rootCtx = useContext(SignalTestContext);
  const ownSelected = useSignal<string[]>([]);
  const choiceMap = useSignal<Record<string, string>>({});
  const isOpen = useSignal(false);
  const containerRef = useRef<HTMLElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  const selectedValues: string[] = rootCtx
    ? (rootCtx.selected.value[name] ?? [])
    : ownSelected.value;

  const getHost = (): Element | null =>
    (containerRef.current?.getRootNode() as ShadowRoot)?.host ?? null;

  const getOptions = (): HTMLElement[] =>
    Array.from(
      getHost()?.querySelectorAll('oip-select-option') ?? []
    ) as HTMLElement[];

  const focusOption = (el: HTMLElement | undefined) =>
    el?.shadowRoot?.querySelector<HTMLElement>('.oip-filter__option')?.focus();

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

  const register = (value: string, label: string, initialSelected = false) => {
    if (choiceMap.value[value] === label) return;
    choiceMap.value = { ...choiceMap.value, [value]: label };
    if (rootCtx) {
      rootCtx.registerOption(name, value, label, initialSelected);
      return;
    }
    if (initialSelected && !ownSelected.value.includes(value)) {
      ownSelected.value = [...ownSelected.value, value];
    }
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

  // Sync selection to ElementInternals.setFormValue so a wrapping <form> captures values.
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
    register,
    toggle,
    moveFocus,
    close,
    isOpen: isOpen.value,
    containerRef,
    buttonRef,
    toggleDropdown,
  };
};
