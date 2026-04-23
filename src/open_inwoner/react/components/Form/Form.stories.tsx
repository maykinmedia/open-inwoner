import { Meta, StoryObj } from '@storybook/preact-vite';
import FormComponent from './FormComponent';
import FormFilterBar from './FormFilterBar';
import FormFilterChips from './FormFilterChips';
import Select from '../Select/Select';
import SelectOption from '../Select/SelectOption';
import FormButton from './FormButton';

const meta: Meta = {
  title: 'Form/Form',
};

export default meta;

type Story = StoryObj;

export const Default: Story = {
  render: () => {
    return (
      <FormComponent>
        <FormFilterBar>
          <Select label="Status" name="status" multiple={true}>
            <SelectOption label="Development" value="0"></SelectOption>
            <SelectOption label="Acceptatie" value="1"></SelectOption>
            <SelectOption label="Productie" value="2"></SelectOption>
          </Select>
          <Select label="Date" name="date" multiple={false}>
            <SelectOption label="Today" value="0"></SelectOption>
            <SelectOption label="Tommorow" value="1"></SelectOption>
            <SelectOption label="Yesterday" value="2"></SelectOption>
          </Select>
          <FormButton>Toon resultaten</FormButton>
        </FormFilterBar>
        <FormFilterChips />
      </FormComponent>
    );
  },
};
