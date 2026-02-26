import {
  FilterState,
  IFilterGroup,
  IFiltersConfig,
} from '@react/components/Filters';
import { useMemo } from 'preact/hooks';
import { useIntl } from 'react-intl';
import { AfvalFilterConfig, AfvalFilterTypes } from '..';

/**
 * Hook tailor made for Mijn Afval filters.
 * Creates both the filterGroups and initialFilterState.
 * @param config
 */
export const useAfvalFilter = (
  config: AfvalFilterConfig
): IFiltersConfig<AfvalFilterTypes> => {
  const intl = useIntl();

  const filterGroups = useMemo(() => {
    const groups: IFilterGroup<AfvalFilterTypes>[] = [];

    if (config.periode) {
      groups.push({
        name: 'periode',
        label: intl.formatMessage({
          id: 'filter.period_filter',
          description: 'The label for the filter period',
          defaultMessage: 'Periode',
        }),
        choices: config.periode.map((choice) => ({
          label: `${intl.formatMessage({
            id: 'filter.period_filter_year_prefix',
            description: 'The prefix for the options of type period',
            defaultMessage: 'Jaar',
          })} ${choice}`,
          value: String(choice),
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
        choices: config.addresses.map((choice) => ({
          label: choice,
          value: choice,
        })),
      });
    }

    return groups;
  }, [config]);

  const defaultValues = new URLSearchParams(window.location.search);

  const initialFilterState: FilterState<AfvalFilterTypes> = {
    periode: defaultValues.getAll('periode'),
    adres: defaultValues.getAll('adres'),
    'afval-type': defaultValues.getAll('afval-type'),
  };

  return { initialFilterState, filterGroups };
};
