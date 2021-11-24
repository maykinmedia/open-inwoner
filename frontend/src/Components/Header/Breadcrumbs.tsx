import React, {ReactElement} from 'react';
import {matchPath, useLocation} from 'react-router-dom';
import ChevronRightOutlinedIcon from '@mui/icons-material/ChevronRightOutlined';
import {labelFromSlug, ROUTES} from "../../routes/routes";
import {iRoute} from "../../types/route";
import './Breadcrumbs.scss';
import {Link} from '../Typography/Link';


interface iBreadCrumb {
  part: string,
  path: string,
  route: iRoute,
  label?: string
  shouldRenderIcon?: boolean
}


/**
 * Returns the breadcrumbs based the current location and matched routes.
 * @return {ReactElement}
 */
export function Breadcrumbs(): ReactElement {
  const location = useLocation();

  /**
   * Returns an iBreadCrumb[] based on the current location and matched routes.
   * This is known to be in accurate with :param* routes.
   * @return {iBreadCrumb[]}
   */
  const getBreadCrumbs = (path: string = location.pathname) => {
    // Root required exception.
    if (path === '/') {
      const route = Object.values(ROUTES).find((route: iRoute) => route.path === `/`)

      if (!route) {
        return [];
      }
      return [{part: '', path: '/', route: route, shouldRenderIcon: true}]
    }

    // Recurse routes.
    const paths = path.split('/')
      .reduce((acc: iBreadCrumb[], part: string) => {
        const currentPath = acc.map((breadCrumb) => breadCrumb.part).join('/')
        const path = `${currentPath}/${part}`;

        let label: string|Function = labelFromSlug('?')(part);

        // Try exact match.
        let route = Object.values(ROUTES).find((route: iRoute) => route.path === `/${part}`)

        // Try parameterized route.
        // FIXME: inaccurate because :param* links are not handled correctly.
        if (!route) {
          let routes = Object.values(ROUTES).filter((r: iRoute) => {
            return matchPath(path, {
              path: r.path,
            })
          })

          if (routes.length > 1) {
            routes = routes.filter((r: iRoute) => r.path.match(/\//g)?.length === path.match(/\//g)?.length)
          }
          route = routes[0];
        }

        // Resolve label.
        label = route?.label || label;

        if (typeof label === 'function') {
          label = label(part);
        }

        // Return acc.
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
    if(breadcrumb.part === '') {
      return '';
    }
    return typeof (breadcrumb?.label) === 'string' ? breadcrumb.label : breadcrumb.route?.label as string
  }

  /**
   * Renders the breadcrumbs.
   * @return {ReactElement}
   */
  const renderBreadCrumbs = () => {
    const crumbles = getBreadCrumbs()
    if (crumbles.length > 1) {
      return crumbles.map((breadCrumb: iBreadCrumb, index: number) => {
        const Icon = breadCrumb.route?.icon;

        return (
          <li key={index} className="breadcrumbs__list-item">
            {index > 0 && <ChevronRightOutlinedIcon />}
            <Link active={false} secondary={index < getBreadCrumbs().length - 1} to={breadCrumb.path}>
              {breadCrumb.shouldRenderIcon && Icon && <Icon />}
              {getBreadCrumbLabel(breadCrumb)}
            </Link>
          </li>
        );
      });
    }
  }

  return (
    <nav className="breadcrumbs">
      <ul className="breadcrumbs__list">
        {renderBreadCrumbs()}
      </ul>
    </nav>
  );
}
