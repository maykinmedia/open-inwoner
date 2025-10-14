import { useState } from 'react'
import { Meta, StoryObj } from '@storybook/react'
import Counter from '@react/components/Counter/Counter'

const meta: Meta<typeof Counter> = {
  title: 'React/Components/Counter',
  component: Counter,
  tags: ['autodocs'],
  argTypes: {
    incrementText: {
      control: 'text',
      description: 'Text for the increment button',
    },
    decrementText: {
      control: 'text',
      description: 'Text for the decrement button',
    },
    resetText: {
      control: 'text',
      description: 'Text for the reset button',
    },
    incrementBgColor: {
      control: 'color',
      description: 'Background color for the increment button',
    },
    decrementBgColor: {
      control: 'color',
      description: 'Background color for the decrement button',
    },
    resetBgColor: {
      control: 'color',
      description: 'Background color for the reset button',
    },
  },
}

export default meta

type Story = StoryObj<typeof Counter>

export const Default: Story = {
  args: {
    incrementText: 'Count increment',
    decrementText: 'Count decrement',
    resetText: 'Reset',
    incrementBgColor: '', // Will use CSS custom property var(--oip-color-info-light)
    decrementBgColor: '', // Will use CSS custom property var(--oip-color-danger-light)
    resetBgColor: '', // Will use CSS custom property var(--oip-color-neutral-light)
  },
  render: (args) => {
    const [count, setCount] = useState(0)
    return (
      <div>
        <div className="counter__result">Count: {count}</div>
        <Counter
          count={count}
          setCount={setCount}
          incrementText={args.incrementText}
          decrementText={args.decrementText}
          resetText={args.resetText}
          incrementBgColor={args.incrementBgColor}
          decrementBgColor={args.decrementBgColor}
          resetBgColor={args.resetBgColor}
        />
      </div>
    )
  },
}
