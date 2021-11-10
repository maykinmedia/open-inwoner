import React, {ComponentType, ReactElement} from 'react';
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
 * @return {ReactElement}
 */
export function Link(props: iLinkProps): ReactElement {
  const {to, activeClassName, children, icon, shouldRenderIcon, ..._props} = props;
  const className = (props.primary) ? 'link link--primary' : 'link';
  const Icon = icon;

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
    <NavLink className={className} activeClassName={activeClassName} to={to} {..._props as any}>
      {renderChildren()}
    </NavLink>
  );
}

Link.defaultProps = {
  activeClassName: 'link--active',
  shouldRenderIcon: true,
}
