import { withLoader } from '@react/lib/decorators/storybook';
import { Meta, StoryObj } from '@storybook/preact';
import { MATERIAL_ICON_DEFINITION, MaterialIcon, MaterialIconProps } from '.';

const meta: Meta<typeof MaterialIcon> = {
  title: 'Components/MaterialIcon',
  component: MaterialIcon,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
The MaterialIcon component renders Google Material Icons using the outlined icon font.

This component provides a consistent way to display Material Design icons throughout the application. All icons are rendered with proper accessibility attributes and use the material-icons-outlined font family.

**Props:**
- \`name\`: The name of a Material Icon (e.g., 'home', 'search', 'settings')
`,
      },
    },
  },
};
export default meta;

type Story = StoryObj<MaterialIconProps>;

export const CustomIconName: Story = {
  name: 'Custom Icon Name',
  args: {
    name: 'home',
  },
  argTypes: {
    name: {
      control: { type: 'text' },
    },
  },
  parameters: {
    docs: {
      description: {
        story: 'Type any string as the icon name.',
      },
    },
  },
};

export const PresetIcons: Story = {
  name: 'Preset Icons',
  args: {
    name: 'mail',
  },
  argTypes: {
    name: {
      control: { type: 'select' },
      options: [
        'home',
        'search',
        'settings',
        'person',
        'mail',
        'description',
        'inbox',
        'inventory_2',
        'group',
        'help_outline',
        'euro',
      ],
    },
  },
  parameters: {
    docs: {
      description: {
        story: 'Choose from predefined icon names.',
      },
    },
  },
};

// Collection of commonly used icons
export const CommonIcons: Story = {
  name: 'Common Icons Collection',
  parameters: {
    docs: {
      description: {
        story:
          'A collection of commonly used Material Icons in the application.',
      },
    },
  },
  render: () => (
    <div
      style={{
        display: 'flex',
        gap: '20px',
        flexWrap: 'wrap',
        alignItems: 'center',
      }}
    >
      <div style={{ textAlign: 'center' }}>
        <MaterialIcon name="home" />
        <div style={{ fontSize: '12px', marginTop: '5px' }}>home</div>
      </div>
      <div style={{ textAlign: 'center' }}>
        <MaterialIcon name="search" />
        <div style={{ fontSize: '12px', marginTop: '5px' }}>search</div>
      </div>
      <div style={{ textAlign: 'center' }}>
        <MaterialIcon name="settings" />
        <div style={{ fontSize: '12px', marginTop: '5px' }}>settings</div>
      </div>
      <div style={{ textAlign: 'center' }}>
        <MaterialIcon name="person" />
        <div style={{ fontSize: '12px', marginTop: '5px' }}>person</div>
      </div>
      <div style={{ textAlign: 'center' }}>
        <MaterialIcon name="mail" />
        <div style={{ fontSize: '12px', marginTop: '5px' }}>mail</div>
      </div>
      <div style={{ textAlign: 'center' }}>
        <MaterialIcon name="notifications" />
        <div style={{ fontSize: '12px', marginTop: '5px' }}>notifications</div>
      </div>
    </div>
  ),
};

/**
 * Rendered as webcomponent
 */
export const AsWebComponent: Story = {
  args: { name: 'home' },
  decorators: withLoader(MATERIAL_ICON_DEFINITION.tagName),
  render: ({ name }) => <material-icon name={name} />,
};
