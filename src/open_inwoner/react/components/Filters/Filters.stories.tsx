import { Meta, StoryObj } from '@storybook/preact-vite';
import { withLoader } from '@react/lib/decorators';

const meta: Meta = {
  title: 'Components/Filters',
  decorators: withLoader('oip-form'),
  parameters: {
    layout: 'fullscreen',
  },
};

export default meta;

type Story = StoryObj;

/** Default filter bar with two selects and a submit button inside oip-form. */
export const Default: Story = {
  render: () => (
    <oip-form>
      <oip-filters>
        <oip-filter-bar>
          <oip-select label="Status" name="status" multiple={true}>
            <oip-select-option
              label="Development"
              value="development"
            ></oip-select-option>
            <oip-select-option
              label="Acceptatie"
              value="acc"
            ></oip-select-option>
            <oip-select-option
              label="Productie"
              value="prod"
            ></oip-select-option>
          </oip-select>
          <oip-select label="Date" name="date" multiple={false}>
            <oip-select-option label="Today" value="0"></oip-select-option>
            <oip-select-option label="Tomorrow" value="1"></oip-select-option>
            <oip-select-option label="Yesterday" value="2"></oip-select-option>
          </oip-select>
          <oip-form-button>Toon resultaten</oip-form-button>
        </oip-filter-bar>
        <oip-filter-chips />
      </oip-filters>
    </oip-form>
  ),
};

/** Filters with values pre-selected on mount — verifies the value prop and chip rendering. */
export const WithPreselectedValues: Story = {
  render: () => (
    <oip-form>
      <oip-filters>
        <oip-filter-bar>
          <oip-select
            label="Status"
            name="status"
            multiple={true}
            value="development,prod"
          >
            <oip-select-option
              label="Development"
              value="development"
            ></oip-select-option>
            <oip-select-option
              label="Acceptatie"
              value="acc"
            ></oip-select-option>
            <oip-select-option
              label="Productie"
              value="prod"
            ></oip-select-option>
          </oip-select>
          <oip-select label="Date" name="date" multiple={false} value="0">
            <oip-select-option label="Today" value="0"></oip-select-option>
            <oip-select-option label="Tomorrow" value="1"></oip-select-option>
            <oip-select-option label="Yesterday" value="2"></oip-select-option>
          </oip-select>
          <oip-form-button>Toon resultaten</oip-form-button>
        </oip-filter-bar>
        <oip-filter-chips />
      </oip-filters>
    </oip-form>
  ),
};

/** Filter bar with a modal panel for narrow viewports — includes oip-filter-modal and oip-fieldset. */
export const WithModal: Story = {
  render: () => (
    <oip-form>
      <oip-filters>
        <oip-filter-bar>
          <oip-select label="Status" name="status" multiple={true}>
            <oip-select-option
              label="Development"
              value="development"
            ></oip-select-option>
            <oip-select-option
              label="Acceptatie"
              value="acc"
            ></oip-select-option>
            <oip-select-option
              label="Productie"
              value="prod"
            ></oip-select-option>
          </oip-select>
          <oip-form-button>Toon resultaten</oip-form-button>
        </oip-filter-bar>
        <oip-modal>
          <oip-modal-opener slot="opener">
            <oip-filter-modal-opener>Filters</oip-filter-modal-opener>
          </oip-modal-opener>
          <oip-filter-modal>
            <oip-fieldset label="Status" name="status" multiple={true}>
              <oip-fieldset-option
                label="Development"
                value="development"
              ></oip-fieldset-option>
              <oip-fieldset-option
                label="Acceptatie"
                value="acc"
              ></oip-fieldset-option>
              <oip-fieldset-option
                label="Productie"
                value="prod"
              ></oip-fieldset-option>
            </oip-fieldset>
          </oip-filter-modal>
        </oip-modal>
        <oip-filter-chips />
      </oip-filters>
    </oip-form>
  ),
};
