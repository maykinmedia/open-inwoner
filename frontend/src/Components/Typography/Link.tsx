import React, {ComponentType} from 'react';
import {NavLink} from 'react-router-dom';
import './Link.scss';


interface iLinkProps {
  to: string,
  activeClassName?: string | null,
  children?: any
  icon?: ComponentType,
  primary?: boolean,
  shouldRenderIcon?: boolean,
  onClick?: Function
}

/**
 * Generic link component.
 * @param {iLinkProps} props
 * @return {JSX.Element}
 */
export const Link = (props: iLinkProps) => {
  const {to, activeClassName, children, icon, shouldRenderIcon, ..._props} = props;
  const className = (props.primary) ? 'link link--primary' : 'link';
  const Icon = icon;

  return (
    <NavLink className={className} activeClassName={activeClassName} to={to} {..._props as any}>
      {shouldRenderIcon && Icon && <Icon/>}
      {(shouldRenderIcon && Icon) ? children : children || to}
    </NavLink>
  );
}

Link.defaultProps = {
  activeClassName: 'link--active',
  shouldRenderIcon: true,
}
