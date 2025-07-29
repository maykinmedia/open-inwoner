import React from 'react'
import type { Meta, StoryObj } from '@storybook/react'
import Sidenav from './Sidenav'

// Define types for our mock data
interface MockMenuItem {
  href: string
  label: string
  icon: string
  current: boolean
  counter?: number
}

interface SidenavArgs {
  mockData?: MockMenuItem[]
}

// Mock DOM setup for Django data injection
const setupMockDjangoData = (data: MockMenuItem[]) => {
  // Remove existing mock script if present
  const existingScript = document.getElementById('sidenav-menu-data')
  if (existingScript) {
    existingScript.remove()
  }

  // Create mock script element with menu data
  const scriptElement = document.createElement('script')
  scriptElement.id = 'sidenav-menu-data'
  scriptElement.type = 'application/json'
  scriptElement.textContent = JSON.stringify(data)
  document.head.appendChild(scriptElement)

  console.log('Mock data setup complete:', data)
}

// Wrapper component that ensures proper data setup
const SidenavStoryWrapper: React.FC<{ mockData?: MockMenuItem[] }> = ({
  mockData,
}) => {
  React.useEffect(() => {
    console.log('Setting up mock data:', mockData)

    if (mockData && mockData.length > 0) {
      setupMockDjangoData(mockData)
    } else {
      // Clear any existing data for fallback stories
      const existingScript = document.getElementById('sidenav-menu-data')
      if (existingScript) {
        existingScript.remove()
        console.log('Cleared existing mock data')
      }
    }
  }, [mockData])

  return <Sidenav />
}

const meta: Meta<SidenavArgs> = {
  title: 'Components/Navigation/Sidenav',
  component: SidenavStoryWrapper,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
Side navigation component that integrates with Django backend data.
The component reads menu data from a script tag injected by Django and transforms it for the DenHaag SideNavigation component.

## Features
- Django integration via script tag data injection
- Material Icons support
- Fallback navigation when no Django data is available
- Support for counters and current state indicators
        `,
      },
    },
  },
  decorators: [
    (Story) => (
      <div
        style={{
          maxWidth: '300px',
          height: '400px',
          border: '1px solid #e0e0e0',
        }}
      >
        <Story />
      </div>
    ),
  ],
  argTypes: {
    mockData: {
      table: {
        disable: true, // Hide this from controls
      },
    },
  },
}

export default meta
type Story = StoryObj<SidenavArgs>

export const Default: Story = {
  name: 'Default (Fallback)',
  parameters: {
    docs: {
      description: {
        story:
          'Default state when no Django menu data is available. Shows the fallback profile navigation.',
      },
    },
  },
  // No mockData provided, so fallback will be used
}

export const BasicMenu: Story = {
  name: 'Basic Menu',
  args: {
    mockData: [
      {
        href: '/dashboard/',
        label: 'Dashboard',
        icon: 'dashboard',
        current: false,
      },
      {
        href: '/mijn-profiel/',
        label: 'Mijn Profiel',
        icon: 'person',
        current: true,
      },
      {
        href: '/instellingen/',
        label: 'Instellingen',
        icon: 'settings',
        current: false,
      },
    ],
  },
  parameters: {
    docs: {
      description: {
        story:
          'Basic menu with simple navigation items loaded from Django data.',
      },
    },
  },
}

export const MenuWithCounters: Story = {
  name: 'Menu with Counters',
  args: {
    mockData: [
      {
        href: '/berichten/',
        label: 'Berichten',
        icon: 'mail',
        current: false,
        counter: 5,
      },
      {
        href: '/taken/',
        label: 'Mijn Taken',
        icon: 'task_alt',
        current: true,
        counter: 12,
      },
      {
        href: '/meldingen/',
        label: 'Meldingen',
        icon: 'notifications',
        current: false,
        counter: 3,
      },
      {
        href: '/archief/',
        label: 'Archief',
        icon: 'archive',
        current: false,
      },
    ],
  },
  parameters: {
    docs: {
      description: {
        story: 'Navigation menu showing counter badges on certain items.',
      },
    },
  },
}

export const ExtendedMenu: Story = {
  name: 'Extended Menu',
  args: {
    mockData: [
      {
        href: '/dashboard/',
        label: 'Dashboard',
        icon: 'dashboard',
        current: false,
      },
      {
        href: '/mijn-zaken/',
        label: 'Mijn Zaken',
        icon: 'folder',
        current: true,
        counter: 8,
      },
      {
        href: '/aanvragen/',
        label: 'Aanvragen',
        icon: 'description',
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
        href: '/documenten/',
        label: 'Documenten',
        icon: 'insert_drive_file',
        current: false,
      },
      {
        href: '/mijn-profiel/',
        label: 'Mijn Profiel',
        icon: 'person',
        current: false,
      },
      {
        href: '/instellingen/',
        label: 'Instellingen',
        icon: 'settings',
        current: false,
      },
    ],
  },
  parameters: {
    docs: {
      description: {
        story: 'Complete navigation menu with various sections and menu items.',
      },
    },
  },
}

export const SingleItemCurrent: Story = {
  name: 'Single Current Item',
  args: {
    mockData: [
      {
        href: '/dashboard/',
        label: 'Dashboard',
        icon: 'dashboard',
        current: true,
      },
    ],
  },
  parameters: {
    docs: {
      description: {
        story: 'Menu with only one item marked as current/active.',
      },
    },
  },
}

export const EmptyMenuData: Story = {
  name: 'Empty Menu Data',
  args: {
    mockData: [],
  },
  parameters: {
    docs: {
      description: {
        story:
          'What happens when Django provides empty menu data - should fall back to default.',
      },
    },
  },
}

export const LongLabels: Story = {
  name: 'Long Labels',
  args: {
    mockData: [
      {
        href: '/lange-titel/',
        label: 'Zeer Lange Navigatie Titel Die Mogelijk Wrapt',
        icon: 'description',
        current: false,
      },
      {
        href: '/nog-langere-titel/',
        label: 'Een Nog Veel Langere Titel Voor Navigatie Item Testing',
        icon: 'folder_open',
        current: true,
        counter: 99,
      },
      {
        href: '/gewone-titel/',
        label: 'Gewone Titel',
        icon: 'home',
        current: false,
      },
    ],
  },
  parameters: {
    docs: {
      description: {
        story:
          'Navigation with longer label text to test text wrapping and layout.',
      },
    },
  },
}

// Special story for testing invalid JSON
export const InvalidMenuData: Story = {
  name: 'Invalid Menu Data',
  render: () => {
    React.useEffect(() => {
      // Set up invalid JSON before component renders
      const existingScript = document.getElementById('sidenav-menu-data')
      if (existingScript) {
        existingScript.remove()
      }

      const scriptElement = document.createElement('script')
      scriptElement.id = 'sidenav-menu-data'
      scriptElement.type = 'application/json'
      scriptElement.textContent = '{ invalid json data }'
      document.head.appendChild(scriptElement)

      console.log('Set up invalid JSON data')
    }, [])

    return <Sidenav />
  },
  parameters: {
    docs: {
      description: {
        story:
          'Handling of malformed JSON data from Django - should fall back to default.',
      },
    },
  },
}
