import { FormattedMessage } from 'react-intl';
import { withContextGuard } from '@react/lib/hooks/withContextGuard';
import { useFilterContext, useRequiredFilterContext } from '../Filters/context';
import { useRequiredFormContext } from '../Form/context';
import { Button } from '../Button';

/**
 * oip-filter-chips
 *
 * Renders an active-filter chip for every currently selected field value.
 *
 * Each chip shows the human-readable label (looked up via FilterContext) and
 * a remove button that deselects that individual value. A "Filters wissen"
 * button clears all fields at once. The entire component is hidden when no
 * values are selected.
 *
 * Reads field values and mutation methods from FormContext.
 * Reads display labels from FilterContext.
 * Must be rendered inside both oip-form and oip-filters.
 */
const FilterChips = withContextGuard(useFilterContext, () => {
  const formCtx = useRequiredFormContext();
  const filterCtx = useRequiredFilterContext();

  if (formCtx.isEmpty.value) return null;

  return (
    <div class="oip-filter-chips">
      {Object.entries(formCtx.values.value).map(([fieldName, values]) =>
        values.map((value) => {
          const label = filterCtx.getLabel(fieldName, value);
          return (
            <div key={`${fieldName}-${value}`} class="oip-filter-chip">
              <span class="oip-filter-chip__label">{label}</span>
              <button
                type="button"
                class="oip-filter-chip__remove"
                onClick={() => formCtx.removeValue(fieldName, value)}
                aria-label={`Verwijder filter: ${label}`}
              >
                <material-icon name="close" small />
              </button>
            </div>
          );
        })
      )}
      <oip-form-reset-button>
        <FormattedMessage
          id="filter.reset"
          description="The text on the reset form button"
          defaultMessage="Filters wissen"
        />
      </oip-form-reset-button>
    </div>
  );
});

export default FilterChips;
