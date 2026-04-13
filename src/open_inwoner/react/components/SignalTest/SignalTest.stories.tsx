/**
 * Cross-shadow signal test — mirrors the real filters composition pattern.
 *
 * oip-sig-root  reads JSON config, creates Signal<selected> in context
 *   oip-sig-summary  reads selected + isAnySelected (like oip-filter-chips)
 *   oip-sig-list name="colors"  toggles items (like oip-filter)
 *   oip-sig-list name="sizes"   another group, same signal
 *
 * Pass condition:
 *   - Checking a color updates oip-sig-summary immediately
 *   - Clicking "Clear all" in oip-sig-summary unchecks all oip-sig-list boxes
 *   - Both oip-sig-list components reflect each other's changes via summary
 */
import { withLoader } from '@react/lib/decorators';
import type { Meta, StoryObj } from '@storybook/preact-vite';
import { SIG_ROOT_DEFINITION } from './constants';

const config = {
  groups: [
    { name: 'colors', items: ['Red', 'Green', 'Blue', 'Yellow'] },
    { name: 'sizes', items: ['XS', 'S', 'M', 'L', 'XL'] },
    { name: 'brand', items: ['N', 'A', 'S', 'C', 'R'] },
  ],
};

const meta: Meta = {
  title: 'Debug/SignalTest',
  decorators: [withLoader(SIG_ROOT_DEFINITION.tagName)],
  parameters: { layout: 'padded' },
};

export default meta;

export const CrossShadowSignals: StoryObj = {
  render: () => (
    <>
      <script type="application/json" id="sig-test-data">
        {JSON.stringify(config)}
      </script>
      <oip-sig-root data-id="sig-test-data">
        <oip-sig-summary />
        <oip-sig-list name="colors" />
        <oip-sig-list name="sizes" />
        <oip-sig-list name="brand" checkbox={false} />
      </oip-sig-root>
    </>
  ),
};
