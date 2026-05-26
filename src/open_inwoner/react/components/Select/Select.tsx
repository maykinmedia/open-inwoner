import { useSignal } from '@preact/signals';
import { useMemo, useRef } from 'preact/hooks';
import { normalizeBoolean } from '@react/lib/attributes/attribute';
import { useOnClickOutside } from '@react/lib/hooks/useOnClickOutside';
import { useTypeahead } from '@react/lib/hooks';
import { withContextGuard } from '@react/lib/hooks/withContextGuard';
import { BooleanLike } from '@react/types/attributes';
import clsx from 'clsx';
import { type ComponentChildren } from 'preact';
import { useFilterContext } from '../Filters/context';
import { useFormContext, useRequiredFormContext } from '../Form/context';
import type { OptionBinding } from './context';
import { SelectContext } from './context';
import { focusOption, getOptions, bindMoveFocus } from './utils';

export interface SelectProps {
  name: string;
  label: string;
  /** Comma-separated default selected values, e.g. value="open,afgerond". */
  value?: string;
  /** Whether options behave as checkboxes (true) or radio buttons (false). Default: true. */
  multiple?: BooleanLike;
  children?: ComponentChildren;
}

/**
 * oip-select
 *
 * Dropdown filter field bound to the nearest oip-form and oip-filters contexts.
 * Manages its own open/close state and keyboard navigation; delegates value
 * state to FormContext and label registration to FilterContext.
 *
 * Must be rendered inside both oip-form and oip-filters.
 */
const Select = withContextGuard(
  useFormContext,
  ({
    name,
    label,
    value,
    multiple: multipleProp = true,
    children,
  }: SelectProps) => {
    const multiple = normalizeBoolean(multipleProp);
    const defaultValue = value ? value.split(',').map((v) => v.trim()) : [];

    const formCtx = useRequiredFormContext();
    const filterCtx = useFilterContext();

    const binding = formCtx.register(name, defaultValue);
    const choiceMap = useSignal<Record<string, string>>({});
    const isOpenSignal = useSignal(false);
    const containerRef = useRef<HTMLDivElement>(null);
    const buttonRef = useRef<HTMLButtonElement>(null);

    const getLabelForValue = (v: string): string => choiceMap.value[v] ?? '';
    const typeahead = useTypeahead(
      containerRef,
      getOptions,
      focusOption,
      getLabelForValue
    );

    // ── Dropdown open/close ────────────────────────────────────────────────────

    const close = (): void => {
      isOpenSignal.value = false;
      requestAnimationFrame(() => buttonRef.current?.focus());
    };

    const open = (): void => {
      isOpenSignal.value = true;
      requestAnimationFrame(() => {
        if (containerRef.current)
          focusOption(getOptions(containerRef.current)[0]);
      });
    };

    const toggleDropdown = (): void => (isOpenSignal.value ? close() : open());

    // ── Option registration ────────────────────────────────────────────────────

    const registerOption = (
      optValue: string,
      optLabel: string
    ): OptionBinding => {
      if (choiceMap.value[optValue] !== optLabel) {
        choiceMap.value = { ...choiceMap.value, [optValue]: optLabel };
        if (filterCtx) filterCtx.registerLabel(name, optValue, optLabel);
      }
      return {
        isSelected: binding.value.value.includes(optValue),
        onChange: () => binding.onChange(optValue, multiple),
        moveFocus: bindMoveFocus(containerRef.current),
        close,
        typeahead,
      };
    };

    const ctx = { name, multiple, registerOption, close };
    const isOpen = isOpenSignal.value;

    const selectedCount = binding.value.value.length;
    const buttonLabel =
      selectedCount > 0 ? `${label} (${selectedCount})` : label;

    useOnClickOutside(containerRef, close, !isOpen);

    const handleButtonKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        if (!isOpen) toggleDropdown();
      }
    };

    return (
      <SelectContext.Provider value={ctx}>
        <div class="oip-select" ref={containerRef}>
          <button
            ref={buttonRef}
            type="button"
            class={clsx(
              'oip-select__button',
              isOpen && 'oip-select__button--open'
            )}
            onClick={toggleDropdown}
            onKeyDown={handleButtonKeyDown}
            aria-expanded={isOpen}
            aria-haspopup="listbox"
            id={`filter-${name}`}
          >
            <span class="oip-select__label">{buttonLabel}</span>
            <material-icon name="keyboard_arrow_down" small />
          </button>

          <div
            class={clsx(
              'oip-select__choices',
              isOpen && 'oip-select__choices--open'
            )}
            {...(!isOpen ? { inert: true } : {})}
          >
            {children}
          </div>
        </div>
      </SelectContext.Provider>
    );
  }
);

export default Select;
