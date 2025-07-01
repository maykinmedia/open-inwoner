import { useState } from 'react'
import { createPortal } from 'react-dom'
import Count from '@/components/Count/Count'
import Counter from '@/components/Counter/Counter'

export interface DemoProps {
  countNode: HTMLDivElement | null
  counterNode: HTMLDivElement | null
}

/**
 * Main component to manage everything demo related.
 */
const Demo: React.FC<DemoProps> = ({ countNode, counterNode }) => {
  const [count, setCount] = useState(1)

  return (
    <>
      {countNode && createPortal(<Count count={count} />, countNode)}
      {counterNode &&
        createPortal(
          <Counter count={count} setCount={setCount} />,
          counterNode
        )}
    </>
  )
}

export default Demo
