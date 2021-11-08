import React, {useContext, useState} from 'react';
import {useLocation} from 'react-router-dom';
import KeyboardArrowDownOutlinedIcon from '@mui/icons-material/KeyboardArrowDownOutlined';
import {NAVIGATION} from '../../routes/navigation';
import {globalContext} from '../../store';
import {iMenuItem} from '../../types/menu-item';
import {RouteLink} from '../Typography/RouteLink';
import './PrimaryNavigation.scss'


interface iPrimaryNavigationProps {
  menuItems?: iMenuItem[],
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
  const location = useLocation();
  const [resolvedNavigation, setResolvedNavigation] = useState(props.menuItems);
  const [tick, setTick] = useState(0);

  // Run optionally async children function.
  props.menuItems?.forEach(async (menuItem) => {
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
  const renderMenuItems = (menuItems: iMenuItem[], shouldRenderIcon: boolean) => {
    return (
      <ul className="primary-navigation__list">
        {menuItems.filter && menuItems.filter((menuItem: iMenuItem) => globalState.user || !menuItem.route.loginRequired).map((menuItem: iMenuItem, index: number) => {
          const activeClassName = menuItem.route.path === '/' && location.pathname !== '/' ? '' : undefined;

          return (
            <li key={index} className="primary-navigation__list-item">
              <RouteLink activeClassName={activeClassName} route={menuItem.route} routeParams={menuItem.routeParams}
                         shouldRenderIcon={shouldRenderIcon}>
                {menuItem.label || menuItem.route.label}
                {menuItem.children && <KeyboardArrowDownOutlinedIcon/>}
              </RouteLink>
              {menuItem.children && renderMenuItems(menuItem.children as iMenuItem[], false)}
            </li>
          );
        })}
      </ul>
    );
  }

  return (
    <nav className="primary-navigation">
      {resolvedNavigation && renderMenuItems(resolvedNavigation, true)}
    </nav>
  );
}

PrimaryNavigation.defaultProps = {
  menuItems: NAVIGATION,
}
