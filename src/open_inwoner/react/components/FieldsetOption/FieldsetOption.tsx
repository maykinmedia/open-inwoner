import { withContextGuard } from '@react/lib/hooks/withContextGuard';
import {
  useRequiredFieldsetContext,
  useFieldsetContext,
} from '../Fieldset/context';

export interface FieldsetOptionProps {
  value: string;
  label: string;
}

/**
 * oip-fieldset-option
 *
 * A single checkbox or radio option inside oip-fieldset.
 * Renders as a real accessible <label>/<input> pair — no keyboard shortcut
 * or focus management beyond what the browser provides natively.
 *
 * Must be rendered inside oip-fieldset (FieldsetContext).
 */
const FieldsetOption = withContextGuard(
  useFieldsetContext,
  ({ value, label }: FieldsetOptionProps) => {
    const ctx = useRequiredFieldsetContext();
    const { isSelected, onChange } = ctx.registerOption(value, label);

    return (
      <label class="oip-fieldset-option">
        <input
          class="oip-fieldset-option__input"
          type={ctx.multiple ? 'checkbox' : 'radio'}
          name={ctx.name}
          value={value}
          checked={isSelected}
          onChange={onChange}
        />
        <span class="oip-fieldset-option__label">{label}</span>
      </label>
    );
  }
);

export default FieldsetOption;
