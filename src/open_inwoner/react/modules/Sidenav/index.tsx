import { Root } from 'react-dom/client'
import Sidenav from './Sidenav'
import { AbstractPage } from '@react/lib/abstractPage'

export default class Page extends AbstractPage {
  static reactRoot: Root

  static get rootNode() {
    return document.querySelector('#react-openinwoner-sidenav')!
  }

  static get root() {
    return <Sidenav />
  }
}
