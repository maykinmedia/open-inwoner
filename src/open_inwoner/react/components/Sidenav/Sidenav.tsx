// PERHAPS THIS SHOULD BE HERE in components? ELSE IN 'modules'

// import React from 'react'
// import { SideNavigation } from '@gemeente-denhaag/side-navigation'
//
// // Material Icons component
// const MaterialIcon: React.FC<{ name: string }> = ({ name }) => (
//   <span className="material-icons-outlined" aria-hidden="true">
//     {name}
//   </span>
// )
//
// const Sidenav: React.FC = () => {
//   // Get menu data from Django
//   const getMenuData = () => {
//     const scriptElement = document.getElementById('sidenav-menu-data')
//     if (scriptElement?.textContent) {
//       try {
//         const data = JSON.parse(scriptElement.textContent)
//         console.log('Menu data loaded:', data) // Debug log
//         return data
//       } catch (e) {
//         console.error('Failed to parse menu data:', e)
//       }
//     }
//     return []
//   }
//
//   const menuData = getMenuData()
//
//   // Transform Django menu data to DenHaag format
//   if (menuData.length > 0) {
//     const navigationItems = [
//       menuData.map((item: any) => ({
//         href: item.href,
//         label: item.label,
//         icon: <MaterialIcon name={item.icon} />, // Django provides Material Icons names
//         current: item.current,
//         counter: item.counter || undefined,
//       })),
//     ]
//
//     return <SideNavigation items={navigationItems} />
//   }
//
//   // Fallback - should not be appearing
//   const fallbackItems = [
//     [
//       {
//         href: '/mijn-profiel/',
//         label: 'Mijn Profiel',
//         icon: <MaterialIcon name="person" />,
//         current: false,
//       },
//     ],
//   ]
//
//   return <SideNavigation items={fallbackItems} />
// }
//
// export default Sidenav
