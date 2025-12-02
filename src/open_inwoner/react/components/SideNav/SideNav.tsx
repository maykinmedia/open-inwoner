import {
  SideNavigation,
  SideNavigationProps,
} from '@gemeente-denhaag/side-navigation';
import { MaterialIcon } from '@react/components/MaterialIcon';
import { usePropsOrScriptData } from '@react/lib/json/getJsonScriptData';
import { AnyComponent as FC } from 'preact';
import './SideNav.scss';

export interface MenuItem {
  href: string;
  label: string;
  icon?: string;
  current?: boolean;
  counter?: number;
}

export interface SideNavProps {
  /**
   * Define the menu items.
   * The array inside the array allows to create one navigation,
   * with multiple lists that have a gap in between.
   */
  items?: MenuItem[] | MenuItem[][];
  itemsId?: string;
}

const SideNav: FC<SideNavProps> = ({ items, itemsId }) => {
  if (!items && !itemsId) return <></>;

  // Get data from props or script tag
  const rawData = usePropsOrScriptData<MenuItem[] | MenuItem[][]>(
    items,
    itemsId
  );
  if (!rawData) return <></>;

  // Normalize to MenuItem[][] - check if first element is an array
  const normalized =
    rawData.length > 0 && Array.isArray(rawData[0])
      ? (rawData as MenuItem[][])
      : [rawData as MenuItem[]];

  // Transform menu data to DenHaag format
  const navigationItems = normalized.map((item) =>
    item?.map(({ icon, ...item }) => {
      // Make sure icon names are valid.
      icon = icon === 'euro_outline' ? 'euro' : icon;

      return {
        ...item,
        // Only include icon if it exists and is not empty
        icon: icon && icon.trim() ? <MaterialIcon name={icon} /> : undefined,
      };
    })
  ) satisfies SideNavigationProps['items'];

  return <SideNavigation items={navigationItems} />;
};

export default SideNav;
