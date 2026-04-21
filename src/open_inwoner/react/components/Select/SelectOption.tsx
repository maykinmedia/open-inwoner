import { normalizeBoolean } from '@react/lib/attributes/attribute';
import { BooleanLike } from '@react/types/attributes';
import { type AnyComponent as AC } from 'preact';
import { useEffect, useRef } from 'preact/hooks';
import { useSelectContext } from './context';

export interface OptionProps {
  value: string;
  label: string;
  initialSelected?: BooleanLike;
}

/**
 * oip-select-option
 * Renders a single option row inside its own shadow DOM.
 * The host element has role="option" via ElementInternals (set in constants).
 * The inner div is the focusable/interactive element — the input is aria-hidden
 * and exists only for CSS-driven icon state and form value submission.
 */
const SelectOption: AC<OptionProps> = ({
  value,
  label,
  initialSelected = false,
}) => {
  const ctx = useSelectContext();
  const isSelected = ctx.selectedValues.includes(value);
  const divRef = useRef<HTMLElement>(null);

  useEffect(() => {
    ctx.register(value, label, normalizeBoolean(initialSelected));
  }, []);

  // Keep ElementInternals.ariaSelected in sync for screen readers.
  useEffect(() => {
    const host = (divRef.current?.getRootNode() as ShadowRoot)?.host as any;
    if (host?.internals_) {
      host.internals_.ariaSelected = isSelected ? 'true' : 'false';
    }

    console.log(host.internals_.ariaSelected);
  }, [isSelected]);

  const handleKeyDown = (e: KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        ctx.moveFocus('next');
        break;
      case 'ArrowUp':
        e.preventDefault();
        ctx.moveFocus('prev');
        break;
      case 'Enter':
      case ' ':
        e.preventDefault();
        ctx.toggle(value);
        break;
      case 'Escape':
        e.preventDefault();
        ctx.close();
        break;
    }
  };

  return (
    <div
      ref={divRef as any}
      class="oip-filter__option"
      tabIndex={-1}
      onClick={() => ctx.toggle(value)}
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
        class="oip-filter__option-input"
        onChange={() => ctx.toggle(value)}
      />
      <span class="oip-filter__option-label">
        <span>{label}</span>
      </span>
    </div>
  );
};

export default SelectOption;
