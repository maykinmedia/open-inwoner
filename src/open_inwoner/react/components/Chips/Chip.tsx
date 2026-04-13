import { MaterialIcon } from '../MaterialIcon';

interface ChipProps {
  group: string;
  value: string;
  label: string;
  toggle: (group: string, value: string) => void;
}

/**
 * A single active-filter chip: shows the label and a remove button.
 * Pure presenter — all state lives in Chips via ChipsContext.
 */
const Chip = ({ group, value, label, toggle }: ChipProps) => (
  <div class="oip-filter-chip">
    <span class="oip-filter-chip__label">{label}</span>
    <button
      type="button"
      class="oip-filter-chip__remove"
      onClick={() => toggle(group, value)}
      aria-label={`Remove ${label}`}
    >
      <MaterialIcon name="close" />
    </button>
  </div>
);

export default Chip;
