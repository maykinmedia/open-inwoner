import React, { FC } from 'react'
import './Counter.scss'

interface CounterProps {
  count: number
  setCount: React.Dispatch<React.SetStateAction<number>>
}

const Counter: FC<CounterProps> = (props) => {
  return (
    <div className="counter">
      <button onClick={() => props.setCount(props.count + 1)}>
        Count increment
      </button>
      <button
        disabled={props.count <= 0}
        onClick={() => props.count >= 1 && props.setCount(props.count - 1)}
      >
        Count decrement
      </button>
    </div>
  )
}
export default Counter
