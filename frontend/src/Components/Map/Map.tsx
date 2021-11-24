import React from 'react';
import {ReactElement, useEffect, useState} from 'react';
import './Map.scss';

interface iMapProps {
  fixed: boolean,
  lat: number,
  long: number,
  height: string,
  zoom?: number
}

export function Map(props: iMapProps): ReactElement {
  const {fixed, height, lat, long, zoom, ..._props} = props;
  const [library, setLibrary] = useState<{[index: string]: Function|null}>({});

  useEffect(() => {
    import('react-leaflet').then((module) => {
      const MapContainer = module.MapContainer;
      const TileLayer = module.TileLayer;
      setLibrary({MapContainer, TileLayer})
    });
  }, [])

  const Container = library.MapContainer || function () {return null}
  const TileLayer = library.TileLayer || function () {return null}

  const fixedProps = (fixed) ? {doubleClickZoom: false, dragging: false, scrollWheelZoom: false, zoomControl: false} : {};

  return (
    <Container center={[lat, long]} zoom={zoom} style={{height: height}} {...fixedProps} {..._props}>
      <TileLayer attribution='&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/>
    </Container>
  )
}

Map.defaultProps = {
  zoom: 13
}
