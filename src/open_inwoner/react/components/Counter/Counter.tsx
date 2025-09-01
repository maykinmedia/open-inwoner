import { FC } from 'react'
import './Counter.scss'

interface CounterProps {
  count: number
  setCount: React.Dispatch<React.SetStateAction<number>>
  incrementText?: string
  decrementText?: string
  resetText?: string
  incrementBgColor?: string
  decrementBgColor?: string
  resetBgColor?: string
}

const Counter: FC<CounterProps> = (props) => {
  const {
    count,
    setCount,
    incrementText = 'Count increment',
    decrementText = 'Count decrement',
    resetText = 'Reset',
    incrementBgColor,
    decrementBgColor,
    resetBgColor,
  } = props

  return (
    <div className="counter">
      <button
        className="button button--primary"
        style={{
          backgroundColor: incrementBgColor || 'var(--oip-color-info)',
        }}
        onClick={() => setCount(count + 1)}
      >
        {incrementText}
      </button>
      <button
        className="button button--secondary"
        style={{
          backgroundColor: decrementBgColor || 'var(--oip-color-danger)',
        }}
        disabled={count <= 0}
        onClick={() => count >= 1 && setCount(count - 1)}
      >
        {decrementText}
      </button>
      {resetText && (
        <button
          className="button button--tertiary"
          style={{
            backgroundColor:
              resetBgColor || 'var(--oip-color-neutral-light, #f8f9fa)',
          }}
          onClick={() => setCount(0)}
        >
          {resetText}
        </button>
      )}
    </div>
  )
}

export default Counter
