import { MaterialIcon } from '@react/components/MaterialIcon';
import { AnyComponent as AC } from 'preact';
import { useIntl } from 'react-intl';
import './FilterChip.scss';

export interface FilterChipProps {
  groupName: string;
  groupLabel: string;
  value: string;
  label: string;
  onRemove: (groupName: string, value: string) => void;
}

/**
 * FilterChip - Displays a single selected filter value as a removable chip
 */
const FilterChip: AC<FilterChipProps> = ({
  groupName,
  groupLabel,
  value,
  label,
  onRemove,
}) => {
  const intl = useIntl();

  return (
    <div class="oip-filter-chip">
      <span class="oip-filter-chip__label">{label}</span>
      <button
        type="button"
        class="oip-filter-chip__remove"
        onClick={() => onRemove(groupName, value)}
        aria-label={intl.formatMessage(
          {
            id: 'filter.chip.remove_aria_label',
            description:
              'Accessible label for the button that removes a selected filter chip',
            defaultMessage: 'Verwijder filter {groupLabel}: {label}',
          },
          { groupLabel, label }
        )}
        title={intl.formatMessage(
          {
            id: 'filter.chip.remove_title',
            description:
              'Tooltip for the button that removes a selected filter chip',
            defaultMessage: 'Verwijder filter {label}',
          },
          { label }
        )}
      >
        <MaterialIcon name="close" />
      </button>
    </div>
  );
};

export default FilterChip;
