import React, {ComponentType, ReactElement} from 'react';
import OpenInNewOutlinedIcon from '@mui/icons-material/OpenInNewOutlined';
import {NavLink} from 'react-router-dom';
import './Link.scss';


export interface iLinkProps {
  to: string,
  active?: boolean,
  activeClassName?: string | null,
  children?: any
  icon?: ComponentType,
  iconPosition?: 'before' | 'after',
  primary?: boolean,
  secondary?: boolean,
  shouldRenderIcon?: boolean,
  shouldRenderExternalIcon?: boolean,
  onClick?: Function
}

/**
 * Generic link component.
 * @param {iLinkProps} props
 * @return {ReactElement}
 */
export function Link(props: iLinkProps): ReactElement {
  const {
    to,
    active,
    activeClassName,
    children,
    icon,
    iconPosition,
    primary,
    secondary,
    shouldRenderIcon,
    shouldRenderExternalIcon,
    ..._props
  } = props;
  const Icon = icon;

  /**
   * Returns the className value.
   * @return {string}
   */
  const getClassNames = () => {
    let classNames = 'link';

    if (active) {
      classNames += ' link--active'
    }
    if (iconPosition) {
      classNames += ` button--icon-${iconPosition}`
    }
    if (primary) {
      classNames += ' link--primary'
    }
    if (secondary) {
      classNames += ' link--secondary'
    }
    return classNames;
  }


  /**
   * Renders the children of the link.
   */
  const renderChildren = () => {
    const ExternalIcon = to.startsWith('http') ? <OpenInNewOutlinedIcon/> : null;

    return (
      <>
        {shouldRenderIcon && Icon && <Icon/>}
        {(shouldRenderIcon && Icon) ? children : children || to}
        {shouldRenderExternalIcon && ExternalIcon}
      </>
    );
  };

  // Special cases.
  if (to && to.match('^#') || to.match(':')) {
    return (
      <a className={getClassNames()} href={to} {..._props as any}>
        {renderChildren()}
      </a>
    )
  }

  return (
    <NavLink className={getClassNames()} isActive={() => active} activeClassName={(typeof active === 'boolean') ? null : activeClassName} to={to} {..._props as any}>
      {renderChildren()}
    </NavLink>
  );
}

Link.defaultProps = {
  activeClassName: 'link--active',
  shouldRenderIcon: true,
  shouldRenderExternalIcon: true,
}
