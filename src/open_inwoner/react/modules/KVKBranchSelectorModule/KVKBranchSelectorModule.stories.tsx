import { Meta, StoryObj } from '@storybook/react'
import { IntlProvider } from 'react-intl'
import KVKBranchSelectorModule from './KVKBranchSelectorModule'

const meta: Meta = {
  title: 'React/Modules/KVKBranchSelectorModule',
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
> **👨‍💻 For Developers:** These stories demonstrate Django integration patterns for the KVKBranchSelectorModule. For component usage and features, see the **KVKBranchSelector** stories instead.

**KVKBranchSelectorModule** handles mounting React components from Django templates in eHerkenning flows. It reads configuration from data attributes and branch data from JSON script tags.

**Django Integration Pattern:**

The module automatically initializes components with \`data-react-module="kvkbranchselector"\`:

\`\`\`django
<div data-react-module="kvkbranchselector"
     data-id="branch-selector"
     data-label="Selecteer vestiging"
     data-name="branch_number">
  <script type="application/json" id="branch-data">
    {
      "items": [
        {"id": "rechtspersoon", "label": "Company BV", ...},
        {"id": "000012345678", "label": "Company BV", ...}
      ],
      "selected_id": "000012345678"
    }
  </script>
</div>
\`\`\`

**Module Responsibilities:**
- Reads branch JSON from script tag with \`id="branch-data"\`
- Parses data attributes (\`data-id\`, \`data-label\`, \`data-name\`)
- Creates hidden form input with selected branch value
- Maps \`rechtspersoon\` ID to empty string for Django backend
- Controls submit button enabled/disabled state
- Handles errors gracefully (invalid JSON, missing data)

**Template Helper:**
\`\`\`django
{% react_kvkbranchselector_data company_branches user.vestiging %}
\`\`\`
        `,
      },
    },
  },
  decorators: [
    (Story) => {
      // Create the script tag for branch data (Django would render this)
      const scriptElement = document.createElement('script')
      scriptElement.id = 'branch-data'
      scriptElement.type = 'application/json'

      // Remove existing script if present
      const existingScript = document.getElementById('branch-data')
      if (existingScript) {
        existingScript.remove()
      }

      document.head.appendChild(scriptElement)

      // Create the root element with data attributes (Django would render this)
      const rootElement = document.createElement('div')
      rootElement.id = 'react-kvkbranchselector'
      rootElement.setAttribute('data-react-module', 'kvkbranchselector')
      rootElement.setAttribute('data-id', 'branch-selector')
      rootElement.setAttribute(
        'data-label',
        'Selecteer de vestiging waarmee u wilt inloggen'
      )
      rootElement.setAttribute('data-name', 'branch_number')

      // Remove existing root if present
      const existingRoot = document.getElementById('react-kvkbranchselector')
      if (existingRoot) {
        existingRoot.remove()
      }

      document.body.appendChild(rootElement)

      // Wrap in IntlProvider for translations
      return (
        <div style={{ maxWidth: '500px' }}>
          <IntlProvider
            locale="nl"
            messages={{
              'kvkbranchselector.placeholder':
                'Vul naam, adres of vestigingsnummer in...',
              'kvkbranchselector.clear': 'Wissen',
              'kvkbranchselector.toggle': 'Opties tonen',
            }}
          >
            <Story />
          </IntlProvider>
        </div>
      )
    },
  ],
}

export default meta
type Story = StoryObj

export const BasicUsage: Story = {
  name: 'Basic Django Integration',
  parameters: {
    docs: {
      description: {
        story: `
Shows the basic KVKBranchSelectorModule functionality with branch data loaded from a JSON script tag. This demonstrates the most common use case where Django renders branch items into a script tag and the React module mounts the component, reads the data, and displays the branches.

**Data Source:** JSON script tag with id \`branch-data\`

**Django renders:**
- Script tag with branch array
- Div with data attributes for component configuration
        `,
      },
    },
  },
  render: () => {
    const scriptElement = document.getElementById('branch-data')
    if (scriptElement) {
      scriptElement.textContent = JSON.stringify({
        items: [
          {
            id: 'rechtspersoon',
            label: 'Example Corporation',
            rechtspersoonInfo: '(Rechtspersoon)',
          },
          {
            id: '000038509474',
            label: 'Example Corporation',
            vestigingInfo: 'Vestiging: 000038509474 (Hoofdvestiging)',
            addressInfo: 'Benny Goodmanstraat',
            cityInfo: 'Almere',
            vestigingsnummer: '000038509474',
            type: 'hoofdvestiging',
          },
        ],
        selected_id: null,
      })
    }
    return KVKBranchSelectorModule.root
  },
}

export const WithPreselection: Story = {
  name: 'Preselected Branch from Django',
  parameters: {
    docs: {
      description: {
        story: `
Demonstrates how Django can preselect a branch by setting the \`selected_id\` field in the JSON data. This is useful when a user has previously selected a branch (stored in session or database) and you want to restore their selection.

**Data Source:** JSON script tag with \`selected_id\` set to match a branch

**Django context example:**
\`\`\`python
{
    "items": [...branches...],
    "selected_id": "000038509474"  # From user.vestiging
}
\`\`\`
        `,
      },
    },
  },
  render: () => {
    const scriptElement = document.getElementById('branch-data')
    if (scriptElement) {
      scriptElement.textContent = JSON.stringify({
        items: [
          {
            id: 'rechtspersoon',
            label: 'Example Corporation',
            rechtspersoonInfo: '(Rechtspersoon)',
          },
          {
            id: '000038509474',
            label: 'Example Corporation',
            vestigingInfo: 'Vestiging: 000038509474 (Hoofdvestiging)',
            addressInfo: 'Benny Goodmanstraat',
            cityInfo: 'Almere',
            vestigingsnummer: '000038509474',
            type: 'hoofdvestiging',
          },
        ],
        selected_id: '000038509474', // Preselected vestiging
      })
    }
    return KVKBranchSelectorModule.root
  },
}

export const EmptyBranchesArray: Story = {
  name: 'Empty Branches - Error Handling',
  parameters: {
    docs: {
      description: {
        story: `
Shows how the module handles empty branch data from Django. When Django renders an empty items array \`[]\`, the component gracefully handles this scenario by displaying an error message.

**Scenario:** Empty items array in JSON
**Django might return this when:**
- No branches found in KVK API response
- Company has no registered vestigingen
- API call failed but we still want to render the page

**Fallback:** Error message displayed to user
        `,
      },
    },
  },
  render: () => {
    const scriptElement = document.getElementById('branch-data')
    if (scriptElement) {
      scriptElement.textContent = JSON.stringify({
        items: [],
        selected_id: null,
      })
    }
    return KVKBranchSelectorModule.root
  },
}

export const EmptyScriptContent: Story = {
  name: 'Empty Script Tag - Error Recovery',
  parameters: {
    docs: {
      description: {
        story: `
Demonstrates error recovery when the script tag exists but contains empty content. This can happen during template rendering errors or when no branch data is available from Django.

**Scenario:** Script tag with empty string content
**Causes:**
- Template rendering error
- Missing context variable in Django view
- Empty string rendered instead of JSON

**Fallback:** Module detects empty content and displays error message
        `,
      },
    },
  },
  render: () => {
    const scriptElement = document.getElementById('branch-data')
    if (scriptElement) {
      scriptElement.textContent = ''
    }
    return KVKBranchSelectorModule.root
  },
}

export const InvalidJsonData: Story = {
  name: 'Invalid JSON - Error Handling',
  parameters: {
    docs: {
      description: {
        story: `
Shows the error recovery mechanism when Django renders malformed JSON. This demonstrates robust error handling for production scenarios where template rendering might produce invalid JSON.

**Scenario:** Script tag with invalid JSON syntax
**Causes:**
- Django template rendering issues
- Data corruption
- Unescaped quotes in branch names
- Missing closing brackets

**Error Handling:**
- Module catches JSON.parse() errors
- Logs errors to console for debugging
- Falls back to safe default state
- Application remains stable and doesn't crash
        `,
      },
    },
  },
  render: () => {
    const scriptElement = document.getElementById('branch-data')
    if (scriptElement) {
      scriptElement.textContent = '{ invalid json syntax'
    }
    return KVKBranchSelectorModule.root
  },
}
