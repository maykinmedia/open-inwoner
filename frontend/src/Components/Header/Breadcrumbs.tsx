import React from 'react';
import {Link, useLocation} from 'react-router-dom';
import ChevronRightOutlinedIcon from '@mui/icons-material/ChevronRightOutlined';
import {ROUTES} from "../../routes/routes";
import {iRoute} from "../../types/route";
import './Breadcrumbs.scss';


interface iBreadCrumb {
  part: string,
  path: string,
  route: iRoute,
  label?: string
  shouldRenderIcon?: boolean
}


/**
 * Returns the breadcrumbs based the current location and matched routes.
 * @return {JSX.Element}
 */
export function Breadcrumbs() {
  const location = useLocation();

  /**
   * Returns an iBreadCrumb[] based on the current location and matched routes.
   * @return {iBreadCrumb[]}
   */
  const getBreadCrumbs = () => {
    // Root required exception.
    if (location.pathname === '/') {
      const route = Object.values(ROUTES).find((route: iRoute) => route.path === `/`)

      if (!route) {
        return [];
      }
      return [{part: '', path: '/', route: route, shouldRenderIcon: true}]
    }

    // Recurse routes.
    const paths = location.pathname.split('/')
      .reduce((acc: iBreadCrumb[], part: string) => {
        const currentPath = acc.map((breadCrumb) => breadCrumb.part).join('/')
        const path = `${currentPath}/${part}`;
        let label = null;
        let route = Object.values(ROUTES).find((route: iRoute) => route.path === `/${part}`)

        if (!route) {
          route = Object.values(ROUTES).find((route: iRoute) => route.path.match(`${currentPath}/:[a-zA-Z-_]`))

          if (typeof route?.label === 'function') {
            label = route.label(part);
          }
        }

        return [...acc, {
          part: part,
          label: label,
          path: path,
          route: route,
          shouldRenderIcon: path === '/'
        }] as iBreadCrumb[];
      }, [])
    return paths
  }

  /**
   * Returns the label for the breadcrumb.
   * @param {iBreadCrumb} breadcrumb
   * @return {string}
   */
  const getBreadCrumbLabel = (breadcrumb: iBreadCrumb): string => {
    return breadcrumb.label || breadcrumb.route.label as string;
  }

  /**
   * Renders the breadcrumbs.
   * @return {JSX.Element}
   */
  const renderBreadCrumbs = () => getBreadCrumbs().map((breadCrumb: iBreadCrumb, index: number) => {
    const Icon = breadCrumb.route.icon;
    const linkClassName = (index === getBreadCrumbs().length - 1) ? 'link' : 'link link--active';

    return (
      <li key={index} className="breadcrumbs__list-item">
        {index > 0 && <ChevronRightOutlinedIcon/>}
        <Link className={linkClassName} to={breadCrumb.path}>
          {breadCrumb.shouldRenderIcon && Icon && <Icon/>}
          {getBreadCrumbLabel(breadCrumb)}
        </Link>
      </li>
    );
  });

  return (
    <nav className="breadcrumbs">
      <ul className="breadcrumbs__list">
        {renderBreadCrumbs()}
      </ul>
    </nav>
  );
}
