import { withLoader } from '@react/lib/decorators/storybook';
import type { Meta, StoryObj } from '@storybook/preact';
import {
  KVK_BRANCH_SELECTOR_DEFINITION,
  KVKBranchSelector,
  KVKBranchSelectorProps,
} from '.';

const meta: Meta<KVKBranchSelectorProps> = {
  title: 'Components/KVKBranchSelector',
  component: KVKBranchSelector,
  args: {
    // Default args for all stories
    id: 'branch-selector',
    label: 'Selecteer de vestiging waarmee u wilt inloggen',
    name: 'branch_number',
  },
  argTypes: {
    // Hide props from Storybook controls that aren't useful for the user
    id: {
      control: false,
      description: 'HTML id attribute for the input element',
    },
    name: {
      control: false,
      description: 'Name attribute for form submission (creates hidden input)',
    },
    label: {
      control: 'text',
      description: 'Label text displayed above the combobox',
    },
    branches: {
      control: 'object',
      description: 'Array of branch objects to display in the dropdown',
    },
    selectedBranchId: {
      control: 'text',
      description: 'ID of the initially selected branch',
    },
  },
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
**KVKBranchSelector** is an accessible combobox component for selecting KVK branches (rechtspersoon or vestiging) with search filtering.

**Key Features:**
- Searchable across all branch fields (name, address, city, vestigingsnummer)
- Keyboard navigation (Arrow keys, Enter, Escape, Tab)
- Auto-selects rechtspersoon if available on mount
- Distinguishes branches with identical names using vestigingsnummer
- Form integration with hidden input for Django backend
- Click-outside to close dropdown

**Accessibility:**
- \`role="combobox"\` on input with \`aria-expanded\` and \`aria-controls\`
- \`role="option"\` on list items with \`aria-selected\`
- \`autocomplete="off"\` prevents browser autocomplete conflicts
- Keyboard navigation fully supported
- Screen reader friendly labels and states

**Form Integration:**
- Automatically creates hidden input with specified \`name\`
- Maps 'rechtspersoon' ID to empty string for Django backend
- Enables/disables submit button based on selection state
        `,
      },
    },
  },
};

export default meta;
type Story = StoryObj<KVKBranchSelectorProps>;

// Reusable mock data
const mockBranches = [
  {
    id: 'rechtspersoon',
    label: 'Example Corporation',
    rechtspersoonInfo: '(Rechtspersoon)',
  },
  {
    id: '000012345678',
    label: 'Example Corporation',
    vestigingInfo: 'Vestiging: 000012345678 (Hoofdvestiging)',
    addressInfo: 'Keizersgracht 117',
    cityInfo: 'Amsterdam',
    vestigingsnummer: '000012345678',
    type: 'hoofdvestiging',
  },
  {
    id: '000087654321',
    label: 'Example Corporation',
    vestigingInfo: 'Vestiging: 000087654321',
    addressInfo: 'Wilhelminasingel 1',
    cityInfo: 'Utrecht',
    vestigingsnummer: '000087654321',
    type: 'nevenvestiging',
  },
];

const manyBranches = [
  {
    id: 'rechtspersoon',
    label: 'Example Corporation',
    rechtspersoonInfo: '(Rechtspersoon)',
  },
  ...Array.from({ length: 15 }, (_, i) => ({
    id: `00003${i.toString().padStart(7, '0')}`,
    label: 'Example Corporation',
    vestigingInfo: `Vestiging: 00003${i.toString().padStart(7, '0')}${i === 0 ? ' (Hoofdvestiging)' : ''}`,
    addressInfo: `Straat ${i + 1}`,
    cityInfo: ['Amsterdam', 'Rotterdam', 'Utrecht', 'Den Haag', 'Eindhoven'][
      i % 5
    ],
    vestigingsnummer: `00003${i.toString().padStart(7, '0')}`,
    type: i === 0 ? 'hoofdvestiging' : 'nevenvestiging',
  })),
];

export const Default: Story = {
  args: {
    branches: mockBranches,
  },
  parameters: {
    docs: {
      description: {
        story:
          'Basic usage with rechtspersoon and two branches. The rechtspersoon is auto-selected on mount.',
      },
    },
  },
};

export const WithPreselection: Story = {
  args: {
    branches: mockBranches,
    selectedBranchId: '000012345678',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Shows a preselected vestiging. Notice the vestigingsnummer appears in the input to distinguish it from other branches with the same company name.',
      },
    },
  },
};

export const ManyBranches: Story = {
  args: {
    branches: manyBranches,
  },
  parameters: {
    docs: {
      description: {
        story:
          'Demonstrates scrolling behavior with many branches. Try typing "Rotterdam" or "Straat 5" to see the search filtering in action.',
      },
    },
  },
};

export const SearchFiltering: Story = {
  args: {
    branches: manyBranches,
  },
  parameters: {
    docs: {
      description: {
        story:
          'Focus on search functionality. Type partial matches like "dam" (matches Amsterdam), "000000" (matches vestigingsnummer), or multiple words like "Utrecht Straat" to see multi-word search.',
      },
    },
  },
};

export const InsideForm: Story = {
  args: {
    branches: mockBranches,
  },
  render: (args) => (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        alert('Form submitted! Check console for form data.');
        const formData = new FormData(e.currentTarget);
        console.log('Form data:', Object.fromEntries(formData));
      }}
    >
      <KVKBranchSelector {...args} />
      <div style={{ marginTop: '1rem' }}>
        <button
          type="submit"
          name="submit"
          className="button button--secondary"
          disabled
        >
          Ga door →
        </button>
      </div>
      <p className="utrecht-paragraph">
        💡 Note: The submit button becomes enabled after selecting a branch.
        When selection is cleared, the button becomes disabled.
      </p>
    </form>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Form integration example. Select a branch to enable the submit button. On submit, the hidden input value is logged to console.',
      },
    },
  },
};

export const EmptyBranches: Story = {
  args: {
    branches: [],
  },
  parameters: {
    docs: {
      description: {
        story:
          'Edge case: Empty branches array. The component gracefully handles this by showing no options in the dropdown.',
      },
    },
  },
};

/**
 * Rendered as webcomponent
 */
export const AsWebComponent: Story = {
  args: {
    id: 'kvk-wc-selector',
    label: 'Selecteer de vestiging waarmee u wilt inloggen',
    name: 'branch_number',
    branchesId: 'branches-id',
  },
  decorators: withLoader(KVK_BRANCH_SELECTOR_DEFINITION.tagName),
  render: ({ id, label, name, branchesId }) => (
    <>
      <script type="application/json" id={branchesId}>
        {JSON.stringify(mockBranches)}
      </script>
      <kvk-branch-selector
        id={id}
        label={label}
        name={name}
        branches-id={branchesId}
      />
    </>
  ),
};
