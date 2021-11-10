import React, {ComponentType} from 'react';
import {Link} from 'react-router-dom';
import './Button.scss';

interface iButtonProps {
  href?: string,
  icon?: ComponentType,
  size?: 'big' | 'normal',
  type?: 'button' | 'submit' | 'reset' | undefined,
  open?: boolean,
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
  const {href, icon, size, type, open, transparent, children, ..._props} = props;

  /**
   * Returns the className value.
   * @return {string}
   */
  const getClassNames = () => {
    let classNames = 'button';

    if (icon) {
      classNames += ' button--icon'
    }

    if (size) {
      classNames += ` button--${size}`
    }

    if (open) {
      classNames += ' button--open';
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
