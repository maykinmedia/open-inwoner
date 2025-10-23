import { getJsonFromScriptTag } from '@react/lib/getJsonScriptData'
import ReactDOM from 'react-dom/client'
import ActionList, { IActionProps } from './ActionList'

class ActionListWebComponent extends HTMLElement {
  constructor() {
    super()
  }

  connectedCallback() {
    const actions = getJsonFromScriptTag<IActionProps[]>('userfeed_json')
    if (!actions) return

    const root = ReactDOM.createRoot(this)
    root.render(<ActionList actions={actions} />)
  }
}

export default ActionListWebComponent
