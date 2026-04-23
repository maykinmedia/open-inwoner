import FormButton from '@react/components/Form/FormButton';
import FormComponent from '@react/components/Form/FormComponent';
import FormFilterBar from '@react/components/Form/FormFilterBar';
import FormFilterChips from '@react/components/Form/FormFilterChips';
import FormFilters from '@react/components/Form/FormFilters';
import Select from '@react/components/Select/Select';
import SelectOption from '@react/components/Select/SelectOption';
import { usePropsOrScriptData } from '@react/lib/json';
import { AnyComponent as AC } from 'preact';
import { useAfvalFilter } from './hooks/useAfvalFilters';

export interface AfvalFilterConfig {
  addresses: string[];
  afval_types: Array<{ value: string; label: string }>;
  periode: number[];
}

export type AfvalFilterTypes = 'periode' | 'adres' | 'afval-type';

export type IAfvalFilterProps = {
  /**
   * Used by web components to load config from a `<script type="application/json">` tag.
   */
  dataId?: string;
  /**
   * Used by Preact components (e.g. Storybook) to pass config directly.
   */
  data?: AfvalFilterConfig;
};

const AfvalFilter: AC<IAfvalFilterProps> = ({ data, dataId }) => {
  const config = usePropsOrScriptData<AfvalFilterConfig>(data, dataId);
  if (!config) return null;

  const { filterGroups, initialFilterState } = useAfvalFilter(config);

  return (
    <FormComponent>
      <FormFilters>
        <FormFilterBar>
          {filterGroups.map((group) => (
            <Select
              key={group.name}
              name={group.name}
              label={group.label}
              multiple={group.multiple ?? true}
              value={initialFilterState[group.name].join(',')}
            >
              {group.choices.map((choice) => (
                <SelectOption
                  key={choice.value}
                  value={choice.value}
                  label={choice.label}
                />
              ))}
            </Select>
          ))}
          <FormButton />
        </FormFilterBar>
        <FormFilterChips />
      </FormFilters>
    </FormComponent>
  );
};

export default AfvalFilter;
