import { type AnyComponent as AC } from 'preact';
import { FormattedMessage } from 'react-intl';

/**
 * oip-filter-bar
 *
 * Desktop filter bar (hidden on mobile via CSS). Lays out oip-select fields
 * and an oip-form-button in a horizontal row.
 *
 * The bar is wrapped in a `role="group"` so screen readers announce it as a
 * labelled group of controls. The visible "Filter op:" label is aria-hidden
 * since the group's aria-label covers the same meaning.
 *
 * Pure layout component — all interactive behaviour is owned by
 * FormContext (field state) and FilterContext (submit action).
 */
const FilterBar: AC<{}> = ({ children }) => (
  <div
    class="oip-filter-bar oip-filter-bar--desktop"
    role="group"
    aria-label="Filters"
  >
    <span class="oip-filter-bar__label">
      <FormattedMessage
        id="filter.heading"
        description="The visible label preceding the filter controls"
        defaultMessage="Filter op:"
      />
    </span>
    <div class="oip-filter-bar__filters">{children}</div>
  </div>
);

export default FilterBar;
