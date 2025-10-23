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
        <span>{message} | </span> {title}
      </ActionSingle>
    )
  })
}

export default ActionList
