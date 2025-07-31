import { FC } from 'react'
import { SideNavigation } from '@gemeente-denhaag/side-navigation'
import { MaterialIcon } from '../MaterialIcons/MaterialIcons'

interface MenuItem {
  href: string
  label: string
  icon?: string
  current?: boolean
  counter?: number
}

interface SideNavProps {
  items: MenuItem[]
}

const SideNav: FC<SideNavProps> = ({ items }) => {
  // Transform menu data to DenHaag format
  const navigationItems = [
    items.map((item) => ({
      href: item.href,
      label: item.label,
      // Only include icon if it exists and is not empty
      icon:
        item.icon && item.icon.trim() ? (
          <MaterialIcon name={item.icon} />
        ) : undefined,
      current: item.current,
      counter: item.counter || undefined,
    })),
  ]

  return <SideNavigation items={navigationItems} />
}

export default SideNav
