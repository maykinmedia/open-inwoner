import { type AnyComponent as AC } from 'preact';
import { useEffect, useRef } from 'preact/hooks';
import { useRequiredFormContext } from '../Form/FormContext';
import { useSelectContext } from './context';

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
const SelectOption: AC<OptionProps> = ({ value, label }) => {
  const ctx = useSelectContext();
  const formCtx = useRequiredFormContext();
  const isSelected = formCtx.values.value[ctx.name]?.includes(value) ?? false;
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    ctx.registerLabel(value, label);
  }, []);

  // Keep ElementInternals.ariaSelected in sync for screen readers.
  useEffect(() => {
    const host = (ref.current?.getRootNode() as ShadowRoot)?.host as any;
    if (host?.internals_) {
      host.internals_.ariaSelected = isSelected ? 'true' : 'false';
    }
  }, [isSelected]);

  const toggle = () => formCtx.toggle(ctx.name, value, ctx.multiple);

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
        toggle();
        break;
      case 'Escape':
        e.preventDefault();
        ctx.close();
        break;
    }
  };

  return (
    <div
      ref={ref}
      class="oip-filter__option"
      tabIndex={-1}
      onClick={toggle}
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
        onChange={toggle}
      />
      <span class="oip-filter__option-label">
        <span>{label}</span>
      </span>
    </div>
  );
};

export default SelectOption;
