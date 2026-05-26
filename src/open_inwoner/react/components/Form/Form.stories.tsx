import { Meta, StoryObj } from '@storybook/preact-vite';
import { withLoader } from '@react/lib/decorators';

const meta: Meta = {
  title: 'Form/Form',
  decorators: withLoader('oip-form'),
  parameters: {
    layout: 'fullscreen',
  },
};

export default meta;

type Story = StoryObj;

export const Default: Story = {
  render: () => {
    return (
      <oip-form>
        <oip-filters>
          <oip-filter-bar>
            <oip-form-button>Toon resultaten</oip-form-button>
            <oip-select label="Status" name="status" multiple="true">
              <oip-select-option label="Development" value="development" />
              <oip-select-option label="Acceptatie" value="acc" />
              <oip-select-option label="Productie" value="prod" />
            </oip-select>
            <oip-select label="Date" name="date" multiple={false}>
              <oip-select-option label="Today" value="0" />
              <oip-select-option label="Tommorow" value="1" />
              <oip-select-option label="Yesterday" value="2" />
            </oip-select>
          </oip-filter-bar>
          <oip-modal>
            <oip-modal-opener slot="opener">Filters</oip-modal-opener>
            <oip-filter-modal>
              <oip-fieldset label="Status" name="status" multiple={true}>
                <oip-fieldset-option label="Development" value="development" />
                <oip-fieldset-option
                  label="Acceptatie"
                  value="acc"
                ></oip-fieldset-option>
                <oip-fieldset-option
                  label="Productie"
                  value="prod"
                ></oip-fieldset-option>
              </oip-fieldset>
              <oip-fieldset label="Date" name="date" multiple={false}>
                <oip-fieldset-option
                  label="Today"
                  value="0"
                ></oip-fieldset-option>
                <oip-fieldset-option
                  label="Tommorow"
                  value="1"
                ></oip-fieldset-option>
                <oip-fieldset-option
                  label="Yesterday"
                  value="2"
                ></oip-fieldset-option>
              </oip-fieldset>
            </oip-filter-modal>
          </oip-modal>
          <oip-filter-chips />
        </oip-filters>
      </oip-form>
    );
  },
};

/** Filters with values pre-selected on mount — verifies the value prop and chip rendering. */
export const WithPreselectedValues: Story = {
  render: () => {
    return (
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
              <oip-select-option label="Tommorow" value="1"></oip-select-option>
              <oip-select-option
                label="Yesterday"
                value="2"
              ></oip-select-option>
            </oip-select>
            <oip-form-button>Toon resultaten</oip-form-button>
          </oip-filter-bar>
          <oip-modal>
            <oip-modal-opener slot="opener">Open modal</oip-modal-opener>
            <oip-filter-modal>
              <oip-fieldset
                label="Status"
                name="status"
                multiple={true}
                value="development,prod"
              >
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
              <oip-fieldset label="Date" name="date" multiple={false} value="0">
                <oip-fieldset-option
                  label="Today"
                  value="0"
                ></oip-fieldset-option>
                <oip-fieldset-option
                  label="Tommorow"
                  value="1"
                ></oip-fieldset-option>
                <oip-fieldset-option
                  label="Yesterday"
                  value="2"
                ></oip-fieldset-option>
              </oip-fieldset>
            </oip-filter-modal>
          </oip-modal>
          <oip-filter-chips />
        </oip-filters>
      </oip-form>
    );
  },
};

/** Many options — exercises typeahead search and dropdown scrolling. */
export const ManyOptions: Story = {
  render: () => {
    const years = Array.from({ length: 20 }, (_, i) => 2025 - i);
    const statuses = [
      { value: 'new', label: 'Nieuw' },
      { value: 'open', label: 'Open' },
      { value: 'in_progress', label: 'In behandeling' },
      { value: 'waiting', label: 'Wacht op aanvullende informatie' },
      { value: 'on_hold', label: 'In de wacht' },
      { value: 'resolved', label: 'Opgelost' },
      { value: 'closed', label: 'Gesloten' },
      { value: 'cancelled', label: 'Geannuleerd' },
      { value: 'rejected', label: 'Afgewezen' },
      { value: 'escalated', label: 'Geëscaleerd' },
    ];

    return (
      <oip-form>
        <oip-filters>
          <oip-filter-bar>
            <oip-select label="Jaar" name="jaar" multiple={false}>
              {years.map((year) => (
                <oip-select-option
                  key={year}
                  label={String(year)}
                  value={String(year)}
                ></oip-select-option>
              ))}
            </oip-select>
            <oip-select label="Status" name="status" multiple={true}>
              {statuses.map((s) => (
                <oip-select-option
                  key={s.value}
                  label={s.label}
                  value={s.value}
                ></oip-select-option>
              ))}
            </oip-select>
            <oip-form-button>Toon resultaten</oip-form-button>
          </oip-filter-bar>
          <oip-modal>
            <oip-modal-opener slot="opener">
              <material-icon name="filter_alt" />
              <span class="oip-filter-modal-opener__label">Filters</span>
            </oip-modal-opener>
            <oip-filter-modal>
              <oip-fieldset label="Jaar" name="jaar" multiple={false}>
                {years.map((year) => (
                  <oip-fieldset-option
                    key={year}
                    label={String(year)}
                    value={String(year)}
                  ></oip-fieldset-option>
                ))}
              </oip-fieldset>
              <oip-fieldset label="Status" name="status" multiple={true}>
                {statuses.map((s) => (
                  <oip-fieldset-option
                    key={s.value}
                    label={s.label}
                    value={s.value}
                  ></oip-fieldset-option>
                ))}
              </oip-fieldset>
            </oip-filter-modal>
          </oip-modal>
          <oip-filter-chips />
        </oip-filters>
      </oip-form>
    );
  },
};

/** Single filter — minimal form with one select and no modal. */
export const SingleFilter: Story = {
  render: () => {
    return (
      <oip-form>
        <oip-filters>
          <oip-filter-bar>
            <oip-select label="Periode" name="periode" multiple={false}>
              <oip-select-option label="2025" value="2025"></oip-select-option>
              <oip-select-option label="2024" value="2024"></oip-select-option>
              <oip-select-option label="2023" value="2023"></oip-select-option>
            </oip-select>
            <oip-form-button>Toon resultaten</oip-form-button>
          </oip-filter-bar>
          <oip-filter-chips />
        </oip-filters>
      </oip-form>
    );
  },
};
