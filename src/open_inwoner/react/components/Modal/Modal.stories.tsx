import { Meta, StoryObj } from '@storybook/preact-vite';
import { withLoader } from '@react/lib/decorators';

const meta: Meta = {
  title: 'Components/Modal',
  decorators: withLoader('oip-form', 'oip-modal', 'oip-filter-modal'),
  parameters: {
    layout: 'fullscreen',
  },
};

export default meta;

type Story = StoryObj;

/** Default modal with an opener button and a filter-modal panel. */
export const Default: Story = {
  render: () => (
    <oip-form>
      <oip-filters>
        <oip-modal>
          <oip-modal-opener slot="opener">Open modal</oip-modal-opener>

          <oip-filter-modal>
            <p>Modal content goes here.</p>
          </oip-filter-modal>
        </oip-modal>
      </oip-filters>
    </oip-form>
  ),
};

/** Modal opener with custom label and icon content. */
export const CustomOpener: Story = {
  render: () => (
    <oip-modal>
      <oip-modal-opener slot="opener">
        <material-icon name="filter_alt" />
        <span>Filters</span>
      </oip-modal-opener>

      <p style={{ top: '50%', left: '50%', position: 'fixed' }}>
        Filter panel content.
      </p>
    </oip-modal>
  ),
};
