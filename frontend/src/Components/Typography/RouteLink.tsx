import React, {ComponentType} from 'react';
import {generatePath} from 'react-router-dom';
import {iRoute} from '../../types/route'
import {Link} from './Link';
import './Link.scss';


export interface iRouteLinkProps {
  route: iRoute,
  routeParams: { [index: string]: string },
  activeClassName?: string | null,
  children?: any
  icon?: ComponentType,
  primary?: boolean,
  secondary?: boolean,
  shouldRenderIcon?: boolean,
  onClick?: Function,
}

/**
 * Creates a Link based on a route.
 * @param {iRouteLinkProps} props
 * @return {ReactElement}
 */
export const RouteLink = (props: iRouteLinkProps) => {
  const {route, routeParams, children, icon, ..._props} = props;
  const to = generatePath(route.path, routeParams);
  const Icon = icon || route.icon;

  const label = (typeof route.label === 'function') ? route.label(Object.values(routeParams)) : route.label

  return (
    <Link to={to} icon={Icon} {..._props as any}>
      {children || label}
    </Link>
  );
}

RouteLink.defaultProps = {
  routeParams: {}
}
