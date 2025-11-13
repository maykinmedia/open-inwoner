import { Meta, StoryObj } from '@storybook/react';
import SideNavModule from './SideNavModule';

const meta: Meta = {
  title: 'React/Modules/SideNavModule',
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
SideNavModule is a Django-integrated React component that dynamically loads navigation data from script tags and data attributes. It combines menu items from JSON script tags with optional extra items from data attributes to render a complete side navigation.

**Features:**
- Loads menu data from \`<script id="sidenav-menu-data">\` tags
- Supports additional items via \`data-extra-item\` attributes
- Handles JSON parsing errors gracefully with fallback data
- Integrates seamlessly with Django template rendering
        `,
      },
    },
  },
  decorators: [
    (Story) => {
      const mockJsonScriptElement = document.createElement('script');
      mockJsonScriptElement.id = 'sidenav-menu-data';
      mockJsonScriptElement.type = 'application/json';

      const existingElement = document.getElementById('sidenav-menu-data');
      if (existingElement) {
        existingElement.remove();
      }

      document.head.appendChild(mockJsonScriptElement);

      const mockRootElement = document.createElement('div');
      mockRootElement.id = 'react-openinwoner-sidenav';

      const existingRoot = document.getElementById('react-openinwoner-sidenav');
      if (existingRoot) {
        existingRoot.remove();
      }

      document.body.appendChild(mockRootElement);

      return <Story />;
    },
  ],
};
export default meta;

type Story = StoryObj;

export const BasicNavigation: Story = {
  name: 'Basic Navigation Menu',
  parameters: {
    docs: {
      description: {
        story: `
Shows the basic SideNavModule functionality with a complete navigation menu loaded from JSON script data. This demonstrates the most common use case where Django renders menu items into a script tag and the React component displays them with icons, current state highlighting, and message counters.

**Data Source:** JSON script tag with id \`sidenav-menu-data\`
        `,
      },
    },
  },
  render: () => {
    const scriptElement = document.getElementById('sidenav-menu-data');
    if (scriptElement) {
      scriptElement.textContent = JSON.stringify([
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
      ]);
    }
    return SideNavModule.root;
  },
};

export const ServerComposedNavigation: Story = {
  name: 'Server-Composed Navigation',
  parameters: {
    docs: {
      description: {
        story: `
Demonstrates how SideNavModule now receives complete navigation data from Django server-side composition. All menu items, including conditional items like FAQ links, are composed server-side and provided through a single JSON script tag. This approach is more reliable and performant than client-side data merging.

**Data Source:**
* Complete menu: JSON script tag with id \`sidenav-menu-data\` (includes base menu + conditional items)
* Server-side logic: Django template tag handles all conditional menu composition
        `,
      },
    },
  },
  render: () => {
    const scriptElement = document.getElementById('sidenav-menu-data');
    if (scriptElement) {
      scriptElement.textContent = JSON.stringify([
        {
          href: '/profiel/',
          label: 'Profiel',
          icon: 'person',
          current: false,
        },
        {
          href: '/berichten/',
          label: 'Berichten',
          icon: 'mail',
          current: false,
          counter: 2,
        },
        {
          href: '/general-faq/',
          label: 'Veelgestelde vragen',
          icon: 'question_answer',
          current: false,
          counter: null,
        },
      ]);
    }

    return SideNavModule.root;
  },
};

export const EmptyMenuFallback: Story = {
  name: 'Empty Menu Array - Fallback Data',
  parameters: {
    docs: {
      description: {
        story: `
Shows how SideNavModule handles empty menu data by falling back to default navigation items. When Django renders an empty array \`[]\` to the script tag, the component gracefully displays a fallback "Mijn Profiel" menu item to ensure the navigation remains functional.

* **Scenario:** Empty JSON array in script tag
* **Fallback:** Default "Mijn Profiel" navigation item
        `,
      },
    },
  },
  render: () => {
    const scriptElement = document.getElementById('sidenav-menu-data');
    if (scriptElement) {
      scriptElement.textContent = JSON.stringify([]);
    }
    return SideNavModule.root;
  },
};

export const EmptyScriptFallback: Story = {
  name: 'Empty Script Content - Fallback Data',
  parameters: {
    docs: {
      description: {
        story: `
Demonstrates the fallback behavior when the script tag exists but contains empty content. This can happen during template rendering errors or when no menu data is available. The component detects the empty content and displays the default fallback navigation.

* **Scenario:** Script tag with empty string content
* **Fallback:** Default "Mijn Profiel" navigation item
        `,
      },
    },
  },
  render: () => {
    const scriptElement = document.getElementById('sidenav-menu-data');
    if (scriptElement) {
      scriptElement.textContent = '';
    }
    return SideNavModule.root;
  },
};

export const InvalidJsonFallback: Story = {
  name: 'Invalid JSON - Error Recovery',
  parameters: {
    docs: {
      description: {
        story: `
Shows the error recovery mechanism when the script tag contains malformed JSON. This can occur due to template rendering issues or data corruption. The component catches the JSON parsing error, logs it to the console, and gracefully falls back to the default navigation to maintain application stability.

* **Scenario:** Script tag with invalid JSON syntax
* **Error Handling:** Catches JSON.parse() errors and logs them
* **Fallback:** Default "Mijn Profiel" navigation item
        `,
      },
    },
  },
  render: () => {
    const scriptElement = document.getElementById('sidenav-menu-data');
    if (scriptElement) {
      scriptElement.textContent = '{ invalid json';
    }
    return SideNavModule.root;
  },
};
