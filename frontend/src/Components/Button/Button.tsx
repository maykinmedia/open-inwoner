import React, {ComponentType} from 'react';
import {Link} from 'react-router-dom';
import './Button.scss';

interface iButtonProps {
  href?: string,
  icon?: ComponentType,
  type?: 'button' | 'submit' | 'reset' | undefined,
  open?: boolean,
  transparent?: boolean,
  children?: any,
}


/**
 * A generic button, can be a link or a button.
 * @param {iButtonProps} props
 * @return {JSX.Element}
 */
export function Button(props: iButtonProps) {
  const {href, icon, type, open, transparent, children, ..._props} = props;

  /**
   * Returns the className value.
   * @return {string}
   */
  const getClassNames = () => {
    let classNames = 'button';

    if (icon) {
      classNames += ' button--icon'
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
   * @return {JSX.Element}
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
      return <a className={getClassNames()} href={href}>{getChildren()}</a>;
    }
    return <Link className={getClassNames()} to={href}>{getChildren()}</Link>;
  }
  return <button className={getClassNames()} type={type}>{getChildren()}</button>;
}
