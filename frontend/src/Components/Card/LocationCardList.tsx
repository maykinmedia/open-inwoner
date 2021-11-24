import React, {ReactElement} from 'react';
import {iLocation} from '../../types/pdc';
import {H4} from '../Typography/H4';
import {LocationCard} from './LocationCard';
import './LocationCardList.scss';

interface iLocationCardListProps {
  id?: string,
  locations: iLocation[],
  title?: string
}


/**
 * Renders a location list.
 * @param {iLocationCardListProps} props
 * @return {ReactElement|null}
 */
export function LocationCardList(props: iLocationCardListProps): React.ReactElement | null {
  const {id, locations, title, ..._props} = props;


  /**
   * Returns the list items.
   * @return {ReactElement[]}
   */
  const getListItems = (): ReactElement[] => locations.map((location: iLocation, index: number): ReactElement => {
    return (
      <li key={index} className="location-card-list__list-item">
        <LocationCard location={location}/>
      </li>
    );
  }) || []

  if (!locations.length) {
    return null;
  }

  return (
    <nav className="location-card-list" {..._props}>
      <H4 id={id}>{title}</H4>
      <ul className="location-card-list__list">
        {getListItems()}
      </ul>
    </nav>
  );
}

LocationCardList.defaultProps = {
  title: 'Locaties'
}
