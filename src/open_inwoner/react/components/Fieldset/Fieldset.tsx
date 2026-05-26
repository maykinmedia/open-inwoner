import { normalizeBoolean } from '@react/lib/attributes/attribute';
import { withContextGuard } from '@react/lib/hooks/withContextGuard';
import { BooleanLike } from '@react/types/attributes';
import { type ComponentChildren } from 'preact';
import { useFilterContext } from '../Filters/context';
import { useRequiredFilterContext } from '../Filters/context';
import { useRequiredFormContext } from '../Form/context';
import { FieldsetContext } from './context';

export interface FieldsetProps {
  name: string;
  label: string;
  /** Comma-separated default selected values, e.g. value="open,afgerond". */
  value?: string;
  /** Whether options behave as checkboxes (true) or radio buttons (false). Default: true. */
  multiple?: BooleanLike;
  children?: ComponentChildren;
}

/**
 * oip-fieldset
 *
 * Inline filter field that renders options as visible checkboxes or radio
 * buttons in a flex column list. No dropdown or keyboard navigation — simpler
 * than oip-select and suited for use inside oip-filter-modal.
 *
 * Must be rendered inside both oip-form and oip-filters.
 */
const Fieldset = withContextGuard(
  useFilterContext,
  ({
    name,
    label,
    value,
    multiple: multipleProp = true,
    children,
  }: FieldsetProps) => {
    const multiple = normalizeBoolean(multipleProp);
    const defaultValue = value ? value.split(',').map((v) => v.trim()) : [];

    const formCtx = useRequiredFormContext();
    const filterCtx = useRequiredFilterContext();

    const binding = formCtx.register(name, defaultValue);

    const registerOption = (optValue: string, optLabel: string) => {
      filterCtx.registerLabel(name, optValue, optLabel);
      return {
        isSelected: binding.value.value.includes(optValue),
        onChange: () => binding.onChange(optValue, multiple),
      };
    };

    return (
      <FieldsetContext.Provider value={{ name, multiple, registerOption }}>
        <fieldset class="oip-fieldset">
          <legend class="oip-fieldset__legend">{label}</legend>
          <div class="oip-fieldset__options">{children}</div>
        </fieldset>
      </FieldsetContext.Provider>
    );
  }
);

// @ts-expect-error yes!
Fieldset.formAssociated = true;

export default Fieldset;
