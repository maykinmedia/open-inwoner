import ActionList, { IActionListProps } from './ActionList'
import GenericReactWebComponent from '@react/lib/wc/abstract'

class ActionListWebComponent extends GenericReactWebComponent<IActionListProps> {
  static observedAttributes = ['actions']

  constructor() {
    super(ActionList)
  }
}

export default ActionListWebComponent
