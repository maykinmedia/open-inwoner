import { MaterialIcon } from '@react/components/MaterialIcon';
import { useIsMobile, useOnClickOutside } from '@react/lib/hooks';
import clsx from 'clsx';
import { AnyComponent as AC } from 'preact';
import { type IFilterGroup, useFilterContext } from '../..';
import { useSelect } from '../../hooks/useSelect';
import './Filter.scss';

/**
 * Filter - Individual filter component
 *
 * Renders differently based on isMobile prop:
 * - Desktop: multi-select dropdown with local open/close state
 * - Mobile: section with title and checkbox list
 *
 * Must be used within a FilterWrapper.
 *
 * @example
 * ```tsx
 * <Filter
 *   name="category"
 *   label="Category"
 *   choices={[
 *     { value: 'a', label: 'Option A' },
 *     { value: 'b', label: 'Option B' },
 *   ]}
 * />
 * ```
 */
const Filter: AC<IFilterGroup> = ({
  name,
  label,
  choices,
  multiple = true,
}) => {
  const { selectedFilters, toggleValue, toggleValueRadio } = useFilterContext();

  const isMobile = useIsMobile();
  const Wrapper = isMobile ? 'fieldset' : 'div';
  const selectedValues = selectedFilters[name] || [];
  const selectedCount = selectedValues.length;

  const {
    containerRef,
    isOpen,
    activeIndex,
    handleKeyDown,
    closeDropdown,
    toggleDropdown,
  } = useSelect({ choices, multiple, name, toggleValue, toggleValueRadio });

  const showChoices = isMobile || isOpen;

  // Close dropdown when clicking outside (desktop only)
  useOnClickOutside(containerRef, closeDropdown, isMobile || !isOpen);

  return (
    <Wrapper
      class={clsx(
        'oip-filter',
        isMobile ? 'oip-filter--mobile' : 'oip-filter--dropdown'
      )}
      ref={containerRef as any}
      onKeyDown={isMobile ? undefined : handleKeyDown}
    >
      {isMobile ? (
        <legend className="oip-filter__title" id={`filter-${name}`}>
          {label}
        </legend>
      ) : (
        <button
          type="button"
          className={clsx('oip-filter__button', {
            ['oip-filter__button--open']: showChoices,
          })}
          onClick={toggleDropdown}
          aria-haspopup="listbox"
          aria-expanded={isOpen}
          title={label}
          id={`filter-${name}`}
        >
          <span class="oip-filter__label">
            {selectedCount > 0 ? `${label} (${selectedCount})` : label}
          </span>
          <MaterialIcon name="expand_more" />
        </button>
      )}

      {/* DROPDOWN LIST */}
      {showChoices && (
        <div
          className={'oip-filter__choices'}
          role="listbox"
          aria-labelledby={`filter-${name}`}
          aria-expanded={showChoices}
          aria-activedescendant={
            activeIndex >= 0
              ? `option-${name}-${choices[activeIndex].value}`
              : undefined
          }
        >
          {choices.map((choice, index) => {
            const isChecked = selectedValues.includes(choice.value);

            return (
              <div
                className={clsx('oip-filter__option', {
                  'oip-filter__option--active': index === activeIndex,
                })}
                role="option"
                aria-selected={isChecked}
                key={`${name}.${choice.value}`}
                id={`option-${name}-${choice.value}`}
              >
                <input
                  type={multiple ? 'checkbox' : 'radio'}
                  name={name}
                  class="oip-filter__option-input"
                  id={`${name}.${choice.value}`}
                  value={choice.value}
                  checked={isChecked}
                  tabIndex={isMobile ? undefined : -1}
                  onChange={() => {
                    if (multiple) toggleValue(name, choice.value);
                    else toggleValueRadio(name, choice.value);
                  }}
                />
                <label
                  class="oip-filter__option-label"
                  htmlFor={`${name}.${choice.value}`}
                >
                  <span>{choice.label}</span>
                </label>
              </div>
            );
          })}
        </div>
      )}
    </Wrapper>
  );
};

export default Filter;
