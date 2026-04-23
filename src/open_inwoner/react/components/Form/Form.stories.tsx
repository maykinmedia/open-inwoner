import { Meta, StoryObj } from '@storybook/preact-vite';
import { withLoader } from '@react/lib/decorators';

const meta: Meta = {
  title: 'Form/Form',
  decorators: withLoader('oip-form'),
};

export default meta;

type Story = StoryObj;

export const Default: Story = {
  render: () => {
    return (
      <oip-form>
        <oip-filter-bar>
          <oip-select label="Status" name="status" multiple={true}>
            <oip-select-option
              label="Development"
              value="0"
            ></oip-select-option>
            <oip-select-option label="Acceptatie" value="1"></oip-select-option>
            <oip-select-option label="Productie" value="2"></oip-select-option>
          </oip-select>
          <oip-select label="Date" name="date" multiple={false}>
            <oip-select-option label="Today" value="0"></oip-select-option>
            <oip-select-option label="Tommorow" value="1"></oip-select-option>
            <oip-select-option label="Yesterday" value="2"></oip-select-option>
          </oip-select>
          <oip-form-button>Toon resultaten</oip-form-button>
        </oip-filter-bar>
        <oip-filter-chips />
      </oip-form>
    );
  },
};
