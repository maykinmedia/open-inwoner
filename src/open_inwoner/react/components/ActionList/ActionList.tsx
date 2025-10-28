import { ActionSingle } from '@gemeente-denhaag/action'
import { FC } from 'react'
import './ActionList.scss'

export interface IActionProps {
  title: string
  message: string
  action_url: string
}

export interface IActionListProps {
  actions: IActionProps[]
}

const ActionList: FC<IActionListProps> = ({ actions = [] }) => {
  return actions?.map(({ title, message, action_url: url }, index) => {
    return (
      <ActionSingle key={index} link={url}>
        <span className="denhaag-action__content--oip-message">
          {message} |{' '}
        </span>{' '}
        <span className="denhaag-action__content--oip-title">{title}</span>
      </ActionSingle>
    )
  })
}

export default ActionList
