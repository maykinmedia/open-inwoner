import { Root } from 'react-dom/client'
import Sidenav from './Sidenav'
import { AbstractPage } from '@react/lib/abstractPage'

console.log('Sidenav module loaded')

export default class Page extends AbstractPage {
  static reactRoot: Root

  static get rootNode() {
    return document.querySelector('#react-openinwoner-sidenav')!
  }

  static get root() {
    return <Sidenav />
  }
}
