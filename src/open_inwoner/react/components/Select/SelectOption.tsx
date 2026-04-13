import { normalizeBoolean } from '@react/lib/attributes/attribute';
import { BooleanLike } from '@react/types/attributes';
import { type AnyComponent as AC } from 'preact';
import { useEffect } from 'preact/hooks';
import { useSelectContext } from './context';

export interface OptionProps {
  group: string;
  value: string;
  label: string;
  checkbox?: BooleanLike;
  initialSelected?: BooleanLike;
}

/**
 * oip-sig-option-test
 * Registers itself to the nearest Select on mount via SelectContext,
 * then renders a single checkbox or radio option row.
 */
const SelectOption: AC<OptionProps> = ({
  group,
  value,
  label,
  checkbox = true,
  initialSelected = false,
}) => {
  const { selectedValues, registerChoice, toggle, multiple } =
    useSelectContext();

  const isCheckbox = normalizeBoolean(checkbox);
  const isInitialSelected = normalizeBoolean(initialSelected);

  useEffect(() => {
    registerChoice(value, label, isInitialSelected);
  }, []);

  const isChecked = selectedValues.includes(value);
  const type = isCheckbox && multiple ? 'checkbox' : 'radio';
  const id = `option-${group}-${value}`;

  return (
    <div
      class={`oip-filter__option`}
      role="option"
      aria-selected={isChecked}
      id={id}
    >
      <input
        type={type}
        class="oip-filter__option-input"
        id={`${id}-input`}
        name={group}
        value={value}
        checked={isChecked}
        onChange={() => toggle(value)}
      />
      <label class="oip-filter__option-label" htmlFor={`${id}-input`}>
        <span>{label}</span>
      </label>
    </div>
  );
};

export default SelectOption;
