import { FC } from 'react'
import { FormattedMessage } from 'react-intl'
import './Count.scss'
interface CounterProps {
  count: number
}

const Count: FC<CounterProps> = (props) => {
  return (
    <div className="count">
      <h4>
        <FormattedMessage
          description="Counter"
          defaultMessage="This is the current count"
        />
      </h4>
      <p data-testid="count">{props.count}</p>
    </div>
  )
}
export default Count
