import { useSignal } from '@preact/signals';
import { withContextGuard } from '@react/lib/hooks/withContextGuard';
import { FilterContext } from './context';
import { useFormContext, useRequiredFormContext } from '../Form/context';

/**
 * oip-filters
 *
 * The filter context provider. Must be rendered inside oip-form (FormContext).
 *
 * Responsibilities:
 *   - Maintains the label registry mapping field-name + value → display label.
 *     Labels are registered at mount time by oip-select-option children and
 *     looked up by oip-filter-chips when rendering chip text.
 *   - Implements the concrete submit action: reads current values from the
 *     parent FormContext and navigates to the current pathname with query params.
 *
 * Provides FilterContext to all descendants.
 */
const Filters = withContextGuard(useFormContext, ({ children }) => {
  const formCtx = useRequiredFormContext();
  const optionLabels = useSignal<Record<string, Record<string, string>>>({});

  const registerLabel = (
    fieldName: string,
    value: string,
    label: string
  ): void => {
    const current = optionLabels.value;
    if (current[fieldName]?.[value] === label) return;
    optionLabels.value = {
      ...current,
      [fieldName]: { ...(current[fieldName] ?? {}), [value]: label },
    };
  };

  const getLabel = (fieldName: string, value: string): string =>
    optionLabels.value[fieldName]?.[value] ?? value;

  /**
   * Submit the filter form.
   *
   * Delegates to `formCtx.submit`, passing a handler that serialises the
   * current field values into URL query parameters and navigates to the
   * updated URL. Multiple selected values for the same field are appended
   * as repeated params (e.g. `?status=open&status=closed`).
   *
   * Only GET navigation is performed — no HTML form submission occurs.
   */
  const submit = (): void => {
    formCtx.submit((values) => {
      const params = new URLSearchParams();
      Object.entries(values).forEach(([key, vals]) => {
        vals.forEach((v) => params.append(key, v));
      });
      window.location.assign(`${window.location.pathname}?${params}`);
    });
  };

  return (
    <FilterContext.Provider value={{ registerLabel, getLabel, submit }}>
      <div class="oip-filters">{children}</div>
    </FilterContext.Provider>
  );
});

export default Filters;
