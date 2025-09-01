import type { Meta, StoryObj } from '@storybook/react'

// This page is an example of an unattached doc
const DocsOnly = () => null

const meta: Meta<typeof DocsOnly> = {
  title: 'Introduction',
  component: DocsOnly,
  tags: ['autodocs'],
  parameters: {
    docs: {
      page: () => (
        <div
          style={{
            maxWidth: '800px',
            margin: '0 auto',
            padding: '20px',
            fontFamily: 'system-ui, sans-serif',
          }}
        >
          <h1>Open Inwoner Design System</h1>
          <p>This is the documentation for our component system.</p>
          <h2>What&apos;s included</h2>
          <ul>
            <li>Web components</li>
            <li>React components</li>
            <li>Vanilla JavaScript components</li>
            <li>
              <a
                href="https://www.npmjs.com/package/@open-inwoner/design-tokens"
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: '#1976d2', textDecoration: 'underline' }}
              >
                Open Inwoner Design token-values for NLDS
              </a>
            </li>
          </ul>
          <h2>Getting Started</h2>
          <p>
            Explore the components in the sidebar to see examples and
            documentation.
          </p>
        </div>
      ),
    },
  },
}
export default meta

type Story = StoryObj<typeof DocsOnly>

// Create an unattached docs page
export const Docs: Story = {
  parameters: {
    docs: {
      page: meta.parameters?.docs?.page,
    },
  },
}
