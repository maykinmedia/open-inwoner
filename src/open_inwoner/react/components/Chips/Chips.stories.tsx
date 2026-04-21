import { useSignal, useComputed } from '@preact/signals';
import { SignalTestContext } from '../NewFilter/context';
import type { Meta, StoryObj } from '@storybook/preact-vite';
import Chips from './Chips';

type Story = StoryObj;

const meta: Meta = {
  title: 'Components/Chips',
  component: Chips,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component:
          'Renders a chip for each active filter value plus a clear-all button. Hidden when nothing is selected.',
      },
    },
  },
};

export default meta;

/** Chips with pre-selected values, provided via SignalTestContext. */
export const WithSelection: Story = {
  render: () => {
    const selected = useSignal<Record<string, string[]>>({
      type: ['restafval', 'gft'],
      status: ['open'],
    });
    const isFiltered = useComputed(() =>
      Object.values(selected.value).some((v) => v.length > 0)
    );
    const isDirty = useComputed(() => false);
    const ctx = {
      selected,
      isDirty,
      isFiltered,
      optionLabels: {
        type: { restafval: 'Restafval', gft: 'GFT' },
        status: { open: 'Open' },
      },
      registerOption: () => {},
      toggle: (group: string, value: string) => {
        const current = selected.value[group] ?? [];
        selected.value = {
          ...selected.value,
          [group]: current.includes(value)
            ? current.filter((v) => v !== value)
            : [...current, value],
        };
      },
      toggleRadio: (group: string, value: string) => {
        selected.value = { ...selected.value, [group]: [value] };
      },
      clearAll: () => {
        selected.value = {};
      },
      applyFilters: () => {},
    };

    return (
      <SignalTestContext.Provider value={ctx}>
        <Chips />
      </SignalTestContext.Provider>
    );
  },
};

/** Chips with nothing selected — renders nothing (hidden state). */
export const Empty: Story = {
  render: () => <Chips />,
};
