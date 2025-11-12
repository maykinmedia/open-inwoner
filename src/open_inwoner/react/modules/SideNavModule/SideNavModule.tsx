import { Root } from 'react-dom/client';
import SideNav, { MenuItem } from '@react/components/SideNav/SideNav';
import { AbstractPage } from '@react/lib/abstractPage';
import { getJsonFromScriptTag } from '@react/lib/getJsonScriptData';

export default class SideNavModule extends AbstractPage {
  static reactRoot: Root;

  static get rootNode() {
    return document.querySelector('#react-openinwoner-sidenav')!;
  }

  // Extract menu data from Django
  static getMenuData(): MenuItem[] {
    const data = getJsonFromScriptTag<MenuItem[]>('sidenav-menu-data');

    if (data) {
      console.debug('Menu data loaded:', data);
      return data;
    }

    // Fallback data
    return [
      {
        href: '/mijn-profiel/',
        label: 'Mijn Profiel',
        icon: 'person',
        current: false,
      },
    ];
  }

  static get root() {
    const menuData = this.getMenuData();
    return <SideNav items={[menuData]} />;
  }
}
