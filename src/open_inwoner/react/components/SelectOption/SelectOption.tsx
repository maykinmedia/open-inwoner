import { useEffect, useRef } from 'preact/hooks';
import { withContextGuard } from '@react/lib/hooks/withContextGuard';
import { useSelectContext, useSelectContextNullable } from '../Select/context';

export interface OptionProps {
  value: string;
  label: string;
}

/**
 * oip-select-option
 * Renders a single option row inside its own shadow DOM.
 * The host element has role="option" via ElementInternals (set in constants).
 * The inner div is the focusable/interactive element — the input is aria-hidden
 * and exists only for CSS-driven icon state.
 *
 * Default selection is set on oip-select via the value prop, not here.
 * This component only registers its display label and handles interaction.
 */
const SelectOption = withContextGuard(
  useSelectContextNullable,
  ({ value, label }: OptionProps) => {
    const ctx = useSelectContext();
    const { isSelected, onChange, moveFocus, close, typeahead } =
      ctx.registerOption(value, label);
    const ref = useRef<HTMLDivElement>(null);

    // Keep ElementInternals.ariaSelected in sync for screen readers.
    useEffect(() => {
      const host = (ref.current?.getRootNode() as ShadowRoot)?.host;
      // @ts-expect-error internals_ is only present if this is our custom web-component.
      if (host?.internals_) host.internals_.ariaSelected = String(isSelected);
    }, [isSelected]);

    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          moveFocus('next');
          break;
        case 'ArrowUp':
          e.preventDefault();
          moveFocus('prev');
          break;
        case 'Enter':
        case ' ':
          e.preventDefault();
          onChange();
          break;
        case 'Escape':
          e.preventDefault();
          close();
          break;
        case 'Tab':
          close();
          break;
        default:
          if (
            e.key.length === 1 &&
            !e.ctrlKey &&
            !e.metaKey &&
            !e.altKey &&
            !e.isComposing
          ) {
            typeahead(e.key);
          }
      }
    };

    return (
      <div
        ref={ref}
        class="oip-select-option"
        tabIndex={-1}
        onClick={onChange}
        onKeyDown={handleKeyDown}
      >
        {/* aria-hidden: input is purely for CSS icon state, not exposed to AT */}
        <input
          type={ctx.multiple ? 'checkbox' : 'radio'}
          aria-hidden="true"
          tabIndex={-1}
          name={ctx.name}
          value={value}
          checked={isSelected}
          class="oip-select-option__input"
          onChange={onChange}
        />
        <span class="oip-select-option__label">
          <span>{label}</span>
        </span>
      </div>
    );
  }
);

export default SelectOption;
