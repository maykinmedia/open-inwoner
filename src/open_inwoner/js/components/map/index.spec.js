import { afterEach, describe, expect, it } from 'vitest';
import iconUrl from 'leaflet/dist/images/marker-icon.png';
import shadowUrl from 'leaflet/dist/images/marker-shadow.png';
import { Map } from './index';

const FEATURE_COLLECTION = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [5.1214, 52.0907] },
      properties: { name: 'Stadskantoor' },
    },
  ],
};

function buildMap() {
  document.body.innerHTML = `
    <div class="map__leaflet" data-lat="52.0907" data-lng="5.1214"></div>
  `;
  const node = document.querySelector('.map__leaflet');
  node.dataset.geojsonFeatureCollection = JSON.stringify(FEATURE_COLLECTION);
  new Map(node);
  return node;
}

describe('Map', () => {
  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('renders the markers with the bundled marker images', () => {
    const node = buildMap();

    const icon = node.querySelector('img.leaflet-marker-icon');
    const shadow = node.querySelector('img.leaflet-marker-shadow');

    // Leaflet guesses the image location from leaflet.css, which fails for
    // the hashed file names in the bundle (it then requests `marker-icon.png`
    // relative to the page).
    expect({ icon: icon.src, shadow: shadow.src }).toEqual({
      icon: new URL(iconUrl, document.baseURI).href,
      shadow: new URL(shadowUrl, document.baseURI).href,
    });
  });
});
