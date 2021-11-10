import React, {ComponentType, ReactElement} from 'react';
import {NavLink} from 'react-router-dom';
import './Link.scss';


export interface iLinkProps {
  to: string,
  active?: boolean,
  activeClassName?: string | null,
  children?: any
  icon?: ComponentType,
  primary?: boolean,
  secondary?: boolean,
  shouldRenderIcon?: boolean,
  onClick?: Function
}

/**
 * Generic link component.
 * @param {iLinkProps} props
 * @return {ReactElement}
 */
export function Link(props: iLinkProps): ReactElement {
  const {to, active, activeClassName, children, icon, primary, secondary, shouldRenderIcon, ..._props} = props;
  const Icon = icon;

  let className = 'link';
  if (active) {
    className += ' link--active'
  }
  if (primary) {
    className += ' link--primary'
  }
  if (secondary) {
    className += ' link--secondary'
  }


  /**
   * Renders the children of the link.
   */
  const renderChildren = () => (
    <>
      {shouldRenderIcon && Icon && <Icon/>}
      {(shouldRenderIcon && Icon) ? children : children || to}
    </>
  );

  // Special cases.
  if (to.match('^#') || to.match(':')) {
    return (
      <a className={className} href={to} {..._props as any}>
        {renderChildren()}
      </a>
    )
  }

  return (
    <NavLink className={className} isActive={active} activeClassName={activeClassName} to={to} {..._props as any}>
      {renderChildren()}
    </NavLink>
  );
}

Link.defaultProps = {
  activeClassName: 'link--active',
  shouldRenderIcon: true,
}
