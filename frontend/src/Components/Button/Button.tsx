import React, {ComponentType} from 'react';
import {Link} from 'react-router-dom';
import './Button.scss';


export interface iButtonProps {
  href?: string,
  icon?: ComponentType,
  iconPosition?: 'before' | 'after' | undefined,
  size?: 'big' | 'normal' | undefined,
  type?: 'button' | 'submit' | 'reset' | undefined,
  open?: boolean,
  primary?: boolean
  secondary?: boolean
  transparent?: boolean,
  children?: any,
  [key: string]: any,
}


/**
 * A generic button, can be a link or a button.
 * @param {iButtonProps} props
 * @return {ReactElement}
 */
export function Button(props: iButtonProps) {
  const {href, icon, iconPosition, size, type, open, primary, secondary, transparent, children, ..._props} = props;

  /**
   * Returns the className value.
   * @return {string}
   */
  const getClassNames = () => {
    let classNames = 'button';

    if (icon) {
      classNames += ' button--icon'
    }

    if (iconPosition) {
      classNames += ` button--icon-${iconPosition}`
    }

    if (size) {
      classNames += ` button--${size}`
    }

    if (open) {
      classNames += ' button--open';
    }

    if (primary) {
      classNames += ' button--primary';
    }

    if (secondary) {
      classNames += ' button--secondary';
    }

    if (transparent) {
      classNames += ' button--transparent';
    }
    return classNames;
  };

  /**
   * Returns the children.
   * @return {ReactElement}
   */
  const getChildren = () => {
    const Icon = icon;

    return (
      <>
        {Icon && <Icon/>}
        {children}
      </>
    );
  };

  if (href) {
    if (href.startsWith('http')) {
      return <a className={getClassNames()} href={href} {..._props}>{getChildren()}</a>;
    }
    return <Link className={getClassNames()} to={href} {..._props}>{getChildren()}</Link>;
  }
  return <button className={getClassNames()} type={type} {..._props}>{getChildren()}</button>;
}

Button.defaultProps = {
  iconPosition: 'before',
}
