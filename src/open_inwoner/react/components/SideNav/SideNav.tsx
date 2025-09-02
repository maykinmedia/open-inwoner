import {
  SideNavigation,
  SideNavigationProps,
} from '@gemeente-denhaag/side-navigation'
import { MaterialIcon } from '@react/components/MaterialIcons/MaterialIcons'
import { FC } from 'react'

export interface MenuItem {
  href: string
  label: string
  icon?: string
  current?: boolean
  counter?: number
}

interface SideNavProps {
  /**
   * Define the menu items.
   * The array inside the array allows to create one navigation,
   * with multiple lists that have a gap in between.
   */
  items: MenuItem[][]
}

const SideNav: FC<SideNavProps> = ({ items }) => {
  // Transform menu data to DenHaag format
  const navigationItems: SideNavigationProps['items'] = items.map((item) =>
    item.map(({ icon, ...item }) => {
      // Make sure icon names are valid.
      icon = icon === 'euro_outline' ? 'euro' : icon

      return {
        ...item,
        // TODO remove undefined once https://github.com/nl-design-system/denhaag/issues/1852 is fixed
        counter: undefined,
        // Only include icon if it exists and is not empty
        icon: icon && icon.trim() ? <MaterialIcon name={icon} /> : undefined,
      }
    })
  )

  return <SideNavigation items={navigationItems} />
}

export default SideNav
