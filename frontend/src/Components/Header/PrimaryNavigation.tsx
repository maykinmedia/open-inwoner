import React, {useContext, useState} from 'react';
import {generatePath, Link} from 'react-router-dom';
import KeyboardArrowDownOutlinedIcon from '@mui/icons-material/KeyboardArrowDownOutlined';
import {NAVIGATION} from '../../routes/navigation';
import {globalContext} from '../../store';
import {iMenuItem} from '../../types/menu-item';
import './Link.scss'
import './PrimaryNavigation.scss'


interface iPrimaryNavigationProps {
  menuItems: iMenuItem[],
}

/**
 * Renders the primary navigation.
 * Prop menuItems can be set to contains an iMenuItem[] (defaults to NAVIGATION). Children of top level menu items can
 * contain a "children" key containing either a nested iMenuItem[] or an async function returning a Promise for an
 * iMenuItem[]
 *
 * @return {JSX.Element}
 */
export default function PrimaryNavigation(props: iPrimaryNavigationProps) {
  const {globalState} = useContext(globalContext);
  const [resolvedNavigation, setResolvedNavigation] = useState(props.menuItems);
  const [tick, setTick] = useState(0);

  // Run optionally async children function.
  props.menuItems.forEach(async (menuItem) => {
    if (!menuItem.children) {
      return;
    }

    if (typeof menuItem.children !== "function") {
      return;
    }

    menuItem.children = await menuItem.children()
    setResolvedNavigation(props.menuItems);
    setTick(tick + 1);
  });


  /**
   * Renders menuItems as list.
   * @param {iMenuItem[]} menuItems
   * @param {boolean} shouldRenderIcons=true
   * @return JSX.Element
   */
  const renderMenuItems = (menuItems: iMenuItem[], shouldRenderIcons: boolean) => (
      <ul className="primary-navigation__list">
        {menuItems.filter && menuItems.filter((menuItem: iMenuItem) => globalState.user || !menuItem.route.loginRequired).map((menuItem: iMenuItem, index: number) => {
          const label = (menuItem.label) ? menuItem.label : menuItem.route.label;
          const to = (menuItem.routeParams) ? generatePath(menuItem.route.path, menuItem.routeParams) : menuItem.route.path;
          const Icon = menuItem.route.icon;

          return (
            <li key={index} className="primary-navigation__list-item">
              <Link className="link" to={to}>
                {shouldRenderIcons && Icon && <Icon/>}
                {label}
                {menuItem.children && <KeyboardArrowDownOutlinedIcon/>}
              </Link>
              {menuItem.children && renderMenuItems(menuItem.children as iMenuItem[], false)}
            </li>
          );
        })}
      </ul>
    )

  return (
    <nav className="primary-navigation">
      {renderMenuItems(resolvedNavigation, true)}
    </nav>
  );
}

PrimaryNavigation.defaultProps = {
  menuItems: NAVIGATION,
}
