import { Meta, StoryObj } from '@storybook/react'
import { IntlProvider } from 'react-intl'
import Count from '@react/components/Count/Count'

const messages = {
  'This is the current count': 'Dit is de huidige telling',
}

const meta: Meta<typeof Count> = {
  title: 'React/Components/Count result',
  component: Count,
  decorators: [
    (Story) => (
      <IntlProvider locale="en" messages={messages}>
        <Story />
      </IntlProvider>
    ),
  ],
}
export default meta

type Story = StoryObj<typeof Count>

export const Default: Story = {
  render: (args) => (
    <IntlProvider locale="en" defaultLocale="en">
      <Count {...args} />
    </IntlProvider>
  ),
  args: {
    count: 42,
  },
}
