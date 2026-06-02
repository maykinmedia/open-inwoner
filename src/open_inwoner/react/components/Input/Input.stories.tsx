import type { Meta, StoryObj } from '@storybook/preact';
import Input from './Input';
import type { InputProps } from './Input';

type Story = StoryObj<InputProps>;

const meta: Meta<InputProps> = {
  title: 'Components/Input',
  component: Input,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `A form input field built with Utrecht NLDS components. Provides a label, optional help text, and error messages.

## Anatomy
1. **Label** – describes the field; can be visually hidden (\`noLabel\`) while remaining accessible via \`sr-only\`
2. **Required indicator** – \`aria-hidden\` asterisk appended to the label when \`required\` is set; the \`inputRequired\` attribute on the input signals "required" to screen readers
3. **Input** – Utrecht \`<Textbox>\`; all native attributes (\`type\`, \`placeholder\`, \`disabled\`, \`value\`, …) are forwarded
4. **Help text** – optional guidance rendered as \`<nl-paragraph>\` inside a \`<FormFieldDescription>\` below the input
5. **Error messages** – one \`<FormFieldErrorMessage>\` per entry in the \`errors\` array; only the first receives an \`id\` (used in \`aria-describedby\`)

## Accessibility
- Label is linked to the input via \`htmlFor\`/\`id\` (both use \`name\`).
- Use \`noLabel\` to hide the label visually without removing it from the accessibility tree.
- The required asterisk is \`aria-hidden\` so screen readers announce "required" from the input attribute, not "asterisk".
- The input's \`aria-describedby\` is automatically wired to the help text and first error message when present.
`,
      },
    },
  },
  tags: ['autodocs'],
};

export default meta;

export const Default: Story = {
  args: {
    label: 'Naam',
    name: 'naam',
    placeholder: 'Vul uw naam in',
  },
};

export const Required: Story = {
  args: {
    label: 'E-mailadres',
    name: 'email',
    type: 'email',
    placeholder: 'naam@voorbeeld.nl',
    required: true,
  },
  parameters: {
    docs: {
      description: {
        story:
          'When `required` is set, an `aria-hidden` asterisk is appended to the label and `inputRequired` is set on the input.',
      },
    },
  },
};

export const WithHelpText: Story = {
  args: {
    label: 'Wachtwoord',
    name: 'password',
    type: 'password',
    helpText: 'Minimaal 8 tekens, inclusief een cijfer en een hoofdletter.',
  },
  parameters: {
    docs: {
      description: {
        story:
          '`helpText` renders a paragraph below the input to guide the user.',
      },
    },
  },
};

export const WithErrors: Story = {
  args: {
    label: 'Postcode',
    name: 'postcode',
    value: '1234',
    errors: [
      'Postcode is ongeldig.',
      'Voer een geldige Nederlandse postcode in (bijv. 1234 AB).',
    ],
  },
  parameters: {
    docs: {
      description: {
        story:
          'Each entry in the `errors` array is rendered as a separate error paragraph.',
      },
    },
  },
};

export const HiddenLabel: Story = {
  args: {
    label: 'Zoeken',
    name: 'search',
    type: 'search',
    placeholder: 'Zoeken…',
    noLabel: true,
  },
  parameters: {
    docs: {
      description: {
        story:
          'Setting `noLabel` hides the label visually but keeps it in the accessibility tree. Useful when the surrounding context already provides a visible label (e.g. inside a search bar).',
      },
    },
  },
};

export const Disabled: Story = {
  args: {
    label: 'Gebruikersnaam',
    name: 'username',
    value: 'jan.de.vries',
    disabled: true,
  },
  parameters: {
    docs: {
      description: {
        story:
          'A disabled input cannot be edited and is visually de-emphasised.',
      },
    },
  },
};

export const ReadOnly: Story = {
  args: {
    label: 'BSN',
    name: 'bsn',
    value: '123456789',
    readOnly: true,
    helpText: 'Uw BSN kan niet worden gewijzigd.',
  },
  parameters: {
    docs: {
      description: {
        story:
          '`readOnly` prevents editing while keeping the value selectable and submittable.',
      },
    },
  },
};

export const NumberType: Story = {
  args: {
    label: 'Aantal',
    name: 'aantal',
    type: 'number',
    min: 1,
    max: 100,
    value: 1,
  },
};

export const WithAllStates: Story = {
  name: 'All states overview',
  parameters: {
    docs: {
      description: {
        story: 'Side-by-side overview of the most common Input states.',
      },
    },
  },
  render: () => (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '1.5rem',
        maxWidth: '400px',
      }}
    >
      <Input label="Standaard" name="s1" placeholder="Placeholder tekst" />
      <Input
        label="Verplicht"
        name="s2"
        required
        placeholder="Verplicht veld"
      />
      <Input label="Met hulptekst" name="s3" helpText="Dit is een hulptekst." />
      <Input
        label="Met fout"
        name="s4"
        value="foutief"
        errors={['Dit veld is verplicht.']}
      />
      <Input label="Label verborgen" name="s5" noLabel placeholder="Zoeken…" />
      <Input label="Uitgeschakeld" name="s6" value="niet bewerkbaar" disabled />
      <Input label="Alleen-lezen" name="s7" value="alleen lezen" readOnly />
    </div>
  ),
};
