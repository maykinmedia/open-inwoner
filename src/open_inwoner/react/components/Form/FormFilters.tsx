import { type AnyComponent as AC } from 'preact';

/**
 * oip-filters
 * Wrapper that groups oip-filter-bar and oip-filter-chips.
 * Pure layout component — no form logic.
 */
const FormFilters: AC<{}> = ({ children }) => (
  <div class="oip-filters">{children}</div>
);

export default FormFilters;
