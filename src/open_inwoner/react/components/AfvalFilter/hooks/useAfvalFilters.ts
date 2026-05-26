import { useMemo } from 'preact/hooks';
import { useIntl } from 'react-intl';
import { AfvalFilterConfig, AfvalFilterTypes } from '..';

export interface FilterChoice {
  value: string;
  label: string;
}

export interface FilterGroup {
  name: AfvalFilterTypes;
  label: string;
  choices: FilterChoice[];
  multiple?: boolean;
}

export interface AfvalFilterResult {
  filterGroups: FilterGroup[];
  initialFilterState: Record<AfvalFilterTypes, string[]>;
}

export const useAfvalFilter = (
  config: AfvalFilterConfig
): AfvalFilterResult => {
  const intl = useIntl();

  const filterGroups = useMemo<FilterGroup[]>(() => {
    const groups: FilterGroup[] = [];

    if (config.periode) {
      groups.push({
        name: 'periode',
        label: intl.formatMessage({
          id: 'filter.period_filter',
          description: 'The label for the filter period',
          defaultMessage: 'Periode',
        }),
        choices: config.periode.map((year) => ({
          value: String(year),
          label: `${intl.formatMessage({
            id: 'filter.period_filter_year_prefix',
            description: 'The prefix for the options of type period',
            defaultMessage: 'Jaar',
          })} ${year}`,
        })),
        multiple: false,
      });
    }

    if (config.afval_types) {
      groups.push({
        name: 'afval-type',
        label: intl.formatMessage({
          id: 'filter.container_type_filter',
          description: 'The label for the filter container type',
          defaultMessage: 'Type container',
        }),
        choices: config.afval_types,
      });
    }

    if (config.addresses) {
      groups.push({
        name: 'adres',
        label: intl.formatMessage({
          id: 'filter.adres_filter',
          description: 'The label for the filter adres',
          defaultMessage: 'Adres',
        }),
        choices: config.addresses.map((address) => ({
          value: address,
          label: address,
        })),
      });
    }

    return groups;
  }, [config]);

  const params = new URLSearchParams(window.location.search);
  const initialFilterState: Record<AfvalFilterTypes, string[]> = {
    periode: params.getAll('periode'),
    adres: params.getAll('adres'),
    'afval-type': params.getAll('afval-type'),
  };

  return { filterGroups, initialFilterState };
};
