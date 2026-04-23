import { normalizeBoolean } from '@react/lib/attributes/attribute';
import { useOnClickOutside } from '@react/lib/hooks/useOnClickOutside';
import { BooleanLike } from '@react/types/attributes';
import clsx from 'clsx';
import { type AnyComponent as AC } from 'preact';
import { SelectContext } from './context';
import { useSelectProvider } from './useSelectProvider';

export interface SelectProps {
  name: string;
  label: string;
  /** Comma-separated default selected values, e.g. value="open,afgerond". */
  value?: string;
  /** When true, always show choices without a toggle button (e.g. inside a mobile modal). */
  alwaysOpen?: BooleanLike;
  /** Whether options behave as checkboxes (true) or radio buttons (false). Default: true. */
  multiple?: BooleanLike;
}

const Select: AC<SelectProps> = ({
  name,
  label,
  value,
  alwaysOpen: alwaysOpenProp = false,
  multiple: multipleProp = true,
  children,
}) => {
  const alwaysOpen = normalizeBoolean(alwaysOpenProp);
  const multiple = normalizeBoolean(multipleProp);
  const defaultValue = value ? value.split(',').map((v) => v.trim()) : [];

  const {
    containerRef,
    buttonRef,
    isOpen,
    toggleDropdown,
    selectedValues,
    ...ctx
  } = useSelectProvider(name, multiple, defaultValue);

  useOnClickOutside(containerRef, ctx.close, alwaysOpen || !isOpen);

  const handleButtonKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      if (!isOpen) toggleDropdown();
    }
  };

  if (alwaysOpen) {
    return (
      <SelectContext.Provider value={ctx}>
        <fieldset
          ref={containerRef as any}
          class="oip-filter oip-filter--mobile"
        >
          <legend class="oip-filter__title">{label}</legend>
          <div class="oip-filter__choices">{children}</div>
        </fieldset>
      </SelectContext.Provider>
    );
  }

  return (
    <SelectContext.Provider value={ctx}>
      <div class="oip-filter oip-filter--dropdown" ref={containerRef as any}>
        <button
          ref={buttonRef as any}
          type="button"
          class={clsx('oip-filter__button', {
            'oip-filter__button--open': isOpen,
          })}
          onClick={toggleDropdown}
          onKeyDown={handleButtonKeyDown}
          aria-expanded={isOpen}
          aria-haspopup="listbox"
          id={`filter-${name}`}
        >
          <span class="oip-filter__label">
            {selectedValues.length > 0
              ? `${label} (${selectedValues.length})`
              : label}
          </span>
        </button>

        <div
          class={clsx(
            'oip-filter__choices',
            isOpen && 'oip-filter__choices--open'
          )}
          {...(!isOpen ? { inert: true } : {})}
        >
          {children}
        </div>
      </div>
    </SelectContext.Provider>
  );
};

export default Select;
