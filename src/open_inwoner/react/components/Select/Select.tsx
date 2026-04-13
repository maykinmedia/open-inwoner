import { useOnClickOutside } from '@react/lib/hooks/useOnClickOutside';
import { normalizeBoolean } from '@react/lib/attributes/attribute';
import { BooleanLike } from '@react/types/attributes';
import clsx from 'clsx';
import { type AnyComponent as AC } from 'preact';
import { SelectContext } from './context';
import { useSelectProvider } from './useSelectProvider';

export interface SelectProps {
  name: string;
  label: string;
  /** When true, always show choices without a toggle button (e.g. inside a mobile modal). */
  alwaysOpen?: BooleanLike;
  /** Whether options behave as checkboxes (true) or radio buttons (false). Default: true. */
  multiple?: BooleanLike;
}

/**
 * Renders a labelled group of options as a collapsible dropdown (default) or
 * always-visible fieldset (alwaysOpen).
 *
 * Provides SelectContext so child SelectOption components can self-register
 * and toggle. Bridges up to SignalTestContext automatically when present.
 */
const Select: AC<SelectProps> = ({
  name,
  label,
  alwaysOpen: alwaysOpenProp = false,
  multiple: multipleProp = true,
  children,
}) => {
  const alwaysOpen = normalizeBoolean(alwaysOpenProp);
  const multiple = normalizeBoolean(multipleProp);

  const {
    choices,
    containerRef,
    isOpen,
    activeIndex,
    handleKeyDown,
    closeDropdown,
    toggleDropdown,
    ...ctx
  } = useSelectProvider(name, multiple);

  useOnClickOutside(containerRef, closeDropdown, alwaysOpen || !isOpen);

  if (alwaysOpen) {
    return (
      <SelectContext.Provider value={ctx}>
        <fieldset class="oip-filter oip-filter--mobile">
          <legend class="oip-filter__title">{label}</legend>
          {children}
        </fieldset>
      </SelectContext.Provider>
    );
  }

  return (
    <SelectContext.Provider value={ctx}>
      <div
        class={clsx('oip-filter', 'oip-filter--dropdown')}
        ref={containerRef as any}
        onKeyDown={handleKeyDown}
      >
        <button
          type="button"
          class={clsx('oip-filter__button', {
            'oip-filter__button--open': isOpen,
          })}
          onClick={toggleDropdown}
          aria-expanded={isOpen}
          aria-haspopup="listbox"
          title={label}
          id={`filter-${name}`}
        >
          <span class="oip-filter__label">
            {ctx.selectedValues.length > 0
              ? `${label} (${ctx.selectedValues.length})`
              : label}
          </span>
        </button>

        {/* Always render children so options can self-register on mount. */}
        <div
          class="oip-filter__choices"
          role="listbox"
          aria-labelledby={`filter-${name}`}
          aria-expanded={isOpen}
          aria-activedescendant={
            activeIndex >= 0 && choices[activeIndex]
              ? `option-${name}-${choices[activeIndex].value}`
              : undefined
          }
          style={isOpen ? '' : 'display: none'}
        >
          {children}
        </div>
      </div>
    </SelectContext.Provider>
  );
};

export default Select;
