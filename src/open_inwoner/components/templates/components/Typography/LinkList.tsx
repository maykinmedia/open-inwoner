import React, {ReactElement} from 'react';
import {H4} from './H4';
import {iLinkProps, Link} from './Link';
import {iRouteLinkProps, RouteLink} from './RouteLink';
import './LinkList.scss';


interface iLinkListProps {
  id?: string,
  links: iLinkProps[] | iRouteLinkProps[];
  title?: string
}


/**
 * Renders a link list.
 * @param {iLinkListProps} props
 * @return {ReactElement|null}
 */
export function LinkList(props: iLinkListProps): ReactElement | null {
  const {id, links, title, ..._props} = props;


  /**
   * Returns the list items.
   * @return {ReactElement[]}
   */
  const getListItems = (): ReactElement[] => links.map((linkProps: iLinkProps | iRouteLinkProps, index: number): ReactElement => {
    return (
      <li key={index} className="link-list__list-item">
        {'route' in linkProps && <RouteLink secondary={true} {...linkProps as iRouteLinkProps}/>}
        {'to' in linkProps && <Link secondary={true} {...linkProps as iLinkProps}/>}
      </li>
    );
  }) || []

  if (!links.length) {
    return null;
  }

  return (
    <nav className="link-list" {..._props}>
      <H4 id={id}>{title}</H4>
      <ul className="link-list__list">
        {getListItems()}
      </ul>
    </nav>
  );
}

LinkList.defaultProps = {
  title: 'Links'
}
