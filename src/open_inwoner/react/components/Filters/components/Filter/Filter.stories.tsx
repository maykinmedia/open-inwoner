import { withFilterProvider } from '@react/lib/decorators/storybook';
import type { Meta, StoryObj } from '@storybook/preact-vite';
import { Filter, type IFilterGroup } from '../..';

type Story = StoryObj<IFilterGroup>;

const group = {
  name: 'type-container',
  label: 'Type container',
  choices: [
    { label: 'Restafval', value: 'restafval' },
    { label: 'GFT', value: 'gft' },
    { label: 'Papier', value: 'papier' },
    { label: 'PMD', value: 'pmd' },
  ],
};

const meta: Meta<IFilterGroup> = {
  title: 'Components/Filters/Filter',
  component: Filter,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
Individual filter dropdown component. Renders a button that opens a multi-select dropdown with checkbox options.

Must be used within a FilterProvider context.

**Desktop:** Dropdown button with click-outside-to-close behavior.
**Mobile:** Section with title and inline checkbox list.
        `,
      },
    },
  },
  args: group,
  decorators: [withFilterProvider([group])],
};

export default meta;

/**
 * Default closed dropdown with no selections.
 */
export const Default: Story = {
  args: group,
};

/**
 * Filter with pre-selected values. The button label shows the count.
 */
export const WithSelectedValues: Story = {
  decorators: [
    withFilterProvider([group], { 'type-container': ['restafval', 'gft'] }),
  ],
};

/**
 * Filter with many choices to verify scrolling behavior.
 */
export const ManyChoices: Story = {
  args: {
    name: 'adres',
    label: 'Adres',
    choices: Array.from({ length: 10 }, (_, i) => ({
      label: `Straatnaam ${i + 1}, ${1000 + i} AB, Den Haag`,
      value: `straat-${i + 1}`,
    })),
  },
};

/**
 * Filter with only a single choice.
 */
export const SingleChoice: Story = {
  args: {
    name: 'periode',
    label: 'Periode',
    choices: [{ label: 'Jaar 2024', value: '2024' }],
  },
};

/**
 * Filter with only a single choice.
 */
export const SingleValueChoice: Story = {
  args: {
    name: 'periode',
    label: 'Periode',
    choices: [
      { label: 'Jaar 2024', value: '2024' },
      { label: 'Jaar 2025', value: '2025' },
    ],
    multiple: false,
  },
};
