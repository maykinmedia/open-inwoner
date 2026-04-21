import { useOnClickOutside } from '@react/lib/hooks/useOnClickOutside';
import clsx from 'clsx';
import { ComponentChildren } from 'preact';
import { RefObject } from 'preact';

interface SelectViewProps {
  name: string;
  label: string;
  alwaysOpen: boolean;
  multiple: boolean;
  children: ComponentChildren;
  containerRef: RefObject<HTMLElement>;
  buttonRef: RefObject<HTMLButtonElement>;
  isOpen: boolean;
  selectedValues: string[];
  toggleDropdown: () => void;
  close: () => void;
}

const SelectView = ({
  name,
  label,
  alwaysOpen,
  multiple,
  children,
  containerRef,
  buttonRef,
  isOpen,
  selectedValues,
  toggleDropdown,
  close,
}: SelectViewProps) => {
  useOnClickOutside(containerRef, close, alwaysOpen || !isOpen);

  const handleButtonKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      if (!isOpen) toggleDropdown();
    }
  };

  if (alwaysOpen) {
    return (
      <fieldset ref={containerRef as any} class="oip-filter oip-filter--mobile">
        <legend class="oip-filter__title">{label}</legend>
        <div class="oip-filter__choices">{children}</div>
      </fieldset>
    );
  }

  return (
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

      <div class="oip-filter__choices" inert={!isOpen || undefined}>
        {children}
      </div>
    </div>
  );
};

export default SelectView;
