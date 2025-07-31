import { Root } from 'react-dom/client'
import SideNav from '../../components/SideNav/SideNav'
import { AbstractPage } from '@react/lib/abstractPage'

export default class SideNavModule extends AbstractPage {
  static reactRoot: Root

  static get rootNode() {
    return document.querySelector('#react-openinwoner-sidenav')!
  }

  // Extract menu data from Django
  static getJsonScriptData() {
    const scriptElement = document.getElementById('sidenav-menu-data')
    if (scriptElement?.textContent) {
      try {
        const data = JSON.parse(scriptElement.textContent)
        console.debug('Menu data loaded:', data)
        return data
      } catch (e) {
        console.error('Failed to parse menu data:', e)
      }
    }

    // Fallback data
    return [
      {
        href: '/mijn-profiel/',
        label: 'Mijn Profiel',
        icon: 'person',
        current: false,
      },
    ]
  }

  static get root() {
    const menuData = this.getJsonScriptData()

    return <SideNav items={menuData} />
  }
}
