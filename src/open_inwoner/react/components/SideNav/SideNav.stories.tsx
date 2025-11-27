import { Meta, StoryObj } from '@storybook/preact';
import SideNav, { SideNavProps, loader } from './SideNav';
import 'material-icons/iconfont/material-icons.css';
import { withLoader } from '@react/lib/decorators/storybook-decorators';

const meta: Meta<typeof SideNav> = {
  title: 'Components/SideNav',
  component: SideNav,
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
SideNav is a pure React component that renders navigation menus using the Den Haag design system. It accepts an array of menu items and transforms them into a styled side navigation with support for icons, current state highlighting, and message counters.

**Features:**
- Material Icons integration for navigation icons
- Current page highlighting with visual indicators
- Message/notification counters on menu items
- Responsive design following Den Haag standards
- Flexible item configuration (with or without icons)
- Built on @gemeente-denhaag/side-navigation components

**Props:**
- \`items\`: Array of MenuItem objects with href, label, icon, current state, and optional counter
        `,
      },
    },
  },
};
export default meta;

type Story = StoryObj<SideNavProps>;

export const StandardNavigation: Story = {
  name: 'Standard Navigation',
  parameters: {
    docs: {
      description: {
        story: `
Demonstrates the most common SideNav configuration with icons, current page highlighting, and message counters. This shows how the component handles typical user navigation scenarios with visual feedback for the active page and unread message indicators.

* **Features shown:** Material icons, current state highlighting, message counters
* **Use case:** Main user navigation in citizen portal applications
        `,
      },
    },
  },
  args: {
    items: [
      [
        {
          href: '/mijn-profiel/',
          label: 'Mijn Profiel',
          icon: 'person',
          current: false,
        },
        {
          href: '/mijn-aanvragen/',
          label: 'Mijn Aanvragen',
          icon: 'description',
          current: true,
        },
        {
          href: '/mijn-berichten/',
          label: 'Mijn Berichten',
          icon: 'mail',
          current: false,
          counter: 3,
        },
      ],
    ],
  },
};

export const NotificationCounters: Story = {
  name: 'Message & Notification Counters',
  parameters: {
    docs: {
      description: {
        story: `
Focuses on the counter functionality for displaying unread messages, notifications, or pending items. The component automatically handles counter display styling and positioning according to Den Haag design system standards.

* **Features shown:** Multiple counter variants, notification badges
* **Use case:** Highlighting unread messages, pending actions, or new notifications
        `,
      },
    },
  },
  args: {
    items: [
      [
        {
          href: '/mijn-profiel/',
          label: 'Mijn Profiel',
          icon: 'person',
          current: false,
        },
        {
          href: '/mijn-berichten/',
          label: 'Mijn Berichten',
          icon: 'mail',
          current: false,
          counter: 5,
        },
        {
          href: '/notificaties/',
          label: 'Notificaties',
          icon: 'notifications',
          current: false,
          counter: 12,
        },
      ],
    ],
  },
};

export const TextOnlyNavigation: Story = {
  name: 'Text-Only Navigation',
  parameters: {
    docs: {
      description: {
        story: `
Shows how SideNav handles navigation items without icons, creating a clean text-only interface. This is useful for administrative interfaces, settings pages, or when a simpler visual design is preferred.

* **Features shown:** Text-only navigation items, current state highlighting without icons
* **Use case:** Admin panels, settings sections, or simplified navigation interfaces
        `,
      },
    },
  },
  args: {
    items: [
      [
        {
          href: '/overzicht/',
          label: 'Overzicht',
          current: true,
        },
        {
          href: '/instellingen/',
          label: 'Instellingen',
          current: false,
        },
        {
          href: '/hulp/',
          label: 'Hulp',
          current: false,
        },
      ],
    ],
  },
};

export const MinimalSingleItem: Story = {
  name: 'Single Navigation Item',
  parameters: {
    docs: {
      description: {
        story: `
Demonstrates the component with just one navigation item, useful for specialized pages or single-purpose applications. Shows how the Den Haag side navigation styling adapts to minimal content while maintaining consistent design patterns.

* **Features shown:** Single item navigation, minimal interface
* **Use case:** Specialized applications, landing pages, or focused user flows
        `,
      },
    },
  },
  args: {
    items: [
      [
        {
          href: '/dashboard/',
          label: 'Dashboard',
          icon: 'dashboard',
          current: true,
        },
      ],
    ],
  },
};

export const ComprehensiveNavigation: Story = {
  name: 'Full Application Navigation',
  parameters: {
    docs: {
      description: {
        story: `
Shows a comprehensive navigation menu with multiple sections, representing a full citizen portal application. This demonstrates how the component handles longer navigation lists while maintaining usability and visual hierarchy.

* **Features shown:** Extended navigation menu, mixed content types, scrollable interface
* **Use case:** Complete citizen portal applications with multiple service areas
* **Content:** Includes dashboard, profile, services, messages, finance, documents, and settings
        `,
      },
    },
  },
  args: {
    items: [
      [
        {
          href: '/dashboard/',
          label: 'Dashboard',
          icon: 'dashboard',
          current: false,
        },
        {
          href: '/profiel/',
          label: 'Mijn Profiel',
          icon: 'person',
          current: false,
        },
        {
          href: '/aanvragen/',
          label: 'Mijn Aanvragen',
          icon: 'description',
          current: true,
        },
        {
          href: '/berichten/',
          label: 'Mijn Berichten',
          icon: 'mail',
          current: false,
          counter: 2,
        },
        {
          href: '/financien/',
          label: 'Financiën',
          icon: 'euro',
          current: false,
        },
        {
          href: '/documenten/',
          label: 'Documenten',
          icon: 'folder',
          current: false,
        },
        {
          href: '/instellingen/',
          label: 'Instellingen',
          icon: 'settings',
          current: false,
        },
      ],
    ],
  },
};

export const GroupedNavigationSections: Story = {
  name: 'Grouped Navigation Sections',
  parameters: {
    docs: {
      description: {
        story: `
Demonstrates how SideNav handles multiple navigation groups with logical separations. This shows the advanced capability of organizing navigation items into distinct sections (dashboard, user services, financial tools, system settings) with visual separators between groups.

* **Features shown:** Multi-section navigation, visual group separation, logical content organization
* **Use case:** Complex applications requiring clear navigation hierarchy and content grouping
* **Example Nav Groups:**
  1. **Dashboard**: Primary landing area
  2. **User Services**: Profile, applications, messaging
  3. **Financial**: Finance and document management
  4. **System**: Settings and account management
        `,
      },
    },
  },
  args: {
    items: [
      [
        {
          href: '/dashboard/',
          label: 'Dashboard',
          icon: 'dashboard',
          current: true,
        },
      ],
      [
        {
          href: '/profiel/',
          label: 'Mijn Profiel',
          icon: 'person',
          current: false,
        },
        {
          href: '/aanvragen/',
          label: 'Mijn Aanvragen',
          icon: 'description',
          current: false,
        },
        {
          href: '/berichten/',
          label: 'Mijn Berichten',
          icon: 'mail',
          current: false,
          counter: 2,
        },
      ],
      [
        {
          href: '/financien/',
          label: 'Financiën',
          icon: 'euro',
          current: false,
        },
        {
          href: '/documenten/',
          label: 'Documenten',
          icon: 'folder',
          current: false,
        },
      ],
      [
        {
          href: '/instellingen/',
          label: 'Instellingen',
          icon: 'settings',
          current: false,
        },
        {
          href: '/signout/',
          label: 'Uitloggen',
          icon: 'logout',
          current: false,
        },
      ],
    ],
  },
};

const mockMenuData = [
  {
    href: '/mijn-profiel/',
    label: 'Mijn Profiel',
    icon: 'person',
    current: false,
  },
  {
    href: '/mijn-aanvragen/',
    label: 'Mijn Aanvragen',
    icon: 'description',
    current: true,
  },
  {
    href: '/mijn-berichten/',
    label: 'Mijn Berichten',
    icon: 'mail',
    current: false,
    counter: 3,
  },
];

/**
 * Rendered as webcomponent
 */
export const AsWebComponent: Story = {
  args: { itemsId: 'sidenav-test-data' },
  decorators: withLoader(loader),
  render: ({ itemsId }) => (
    <>
      <script type="application/json" id={itemsId}>
        {JSON.stringify(mockMenuData)}
      </script>
      <side-navigation items-id={itemsId} />
    </>
  ),
};
