import React, {ReactElement} from 'react';
import {iLocation} from '../../types/pdc';
import {Card} from './Card';
import {Map} from '../Map/Map';
import {P} from '../Typography/P';
import './Card.scss';

interface ilocationCardProps {
  location: iLocation,
}


/**
 * A card showing a location.
 * @param {iLocation} props
 * @return {ReactElement}
 */
export function LocationCard(props: ilocationCardProps) {
  const {location, ..._props} = props;

  /**
   * Returns the card header.
   * @return {ReactElement}
   */
  const getHeader = (): ReactElement => {
    const [long, lat] = location.geometry.replace(/^.+?\s/, '')
      .replace(/[()]/, '')
      .split(/\s/)
      .map((str: string):number => parseFloat(str))

    return (

      <Map fixed={true} height='100px' long={long} lat={lat} zoom={15}/>
    );
  };


  return (
    <Card header={getHeader()} title={location.name} {..._props}>
      <P>{location.street} {location.housenumber}<br/>
        {location.postcode} {location.city}</P>
    </Card>
  );
}
