import React from 'react';
import { Link } from 'react-router-dom';
import './Button.scss';

interface ButtonProps {
    href?: string,
    type?: string,
    open?: boolean,
    transparent?: boolean,
    children?: any,
}

export function Button(props:ButtonProps) {
  const getClassNames = () => {
    let classNames = 'button';
    if (props.open) {
      classNames += ' button--open';
    }
    if (props.transparent) {
      classNames += ' button--transparent';
    }
    return classNames;
  };

  if (props.href) {
    if (props.href.startsWith('http')) {
      return <a className={getClassNames()} href={props.href}>{ props.children }</a>;
    }
    return <Link className={getClassNames()} to={props.href}>{ props.children }</Link>;
  }
  return <button className={getClassNames()} type={props.type}>{ props.children }</button>;
}
