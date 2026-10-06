import 'leaflet';
import { RD_CRS } from './rd';
import { isMobile } from '../../lib/device/is-mobile';

/**
 * Creates an element, setting attributes and children without parsing HTML.
 * Using DOM nodes (rather than HTML strings) for popup content prevents XSS
 * through Leaflet's `bindPopup`, which assigns string content via innerHTML.
 * @param {string} tagName
 * @param {Object<string, string>} [attributes]
 * @param {Array<Node|string>} [children]
 * @return {HTMLElement}
 */
function createElement(tagName, attributes = {}, children = []) {
  const element = document.createElement(tagName);
  Object.entries(attributes).forEach(([key, value]) =>
    element.setAttribute(key, value)
  );
  element.append(...children);
  return element;
}

/** @type {NodeListOf<Element>} All the leaflet maps. */
const LEAFLET_MAPS = document.querySelectorAll('.map__leaflet');

/**
 * Renders a (Leaflet) map.
 */
class Map {
  /**
   * Constructor method.
   * @param {HTMLElement} node
   */
  constructor(node) {
    this.node = node;
    this.lat = node.dataset.lat || 52;
    this.lng = node.dataset.lng || 11;
    this.zoom = node.dataset.zoom || 13;
    this.scrollWheelZoom = false;

    const mapOptions = {
      center: L.latLng(this.lat, this.lng),
      scrollWheelZoom: this.scrollWheelZoom,
      zoom: this.zoom,
      crs: RD_CRS,
    };

    const tileConfig = {
      url: `https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/standaard/EPSG:28992/{z}/{x}/{y}.png`,
      options: {
        minZoom: 1,
        maxZoom: 13,
        attribution: `
          Kaartgegevens &copy;
            <a href="https://www.kadaster.nl">Kadaster</a> |
            <a href="https://www.verbeterdekaart.nl">Verbeter de kaart</a>
            `,
      },
    };

    this.map = L.map(this.node, mapOptions);
    const tileLayer = L.tileLayer(tileConfig.url, tileConfig.options);
    tileLayer.addTo(this.map);
    this.addGeoJSON();

    if (isMobile()) {
      this.map.dragging.disable();
    }
  }

  /**
   * Adds geoJSON found in data-geojson-feature-collection.
   */
  addGeoJSON() {
    this.geoJSON = this.node.dataset.geojsonFeatureCollection;

    if (!this.geoJSON) {
      return;
    }

    const data = JSON.parse(this.geoJSON);
    L.geoJSON(data, {
      onEachFeature: (feature, layer) =>
        layer.bindPopup(this.featureToHTML(feature), {
          maxWidth: 300,
        }),
    }).addTo(this.map);
  }

  /**
   * Renders a feature as a DOM node.
   * @param {Object} feature
   * @return {HTMLElement}
   */
  featureToHTML(feature) {
    const {
      name,
      location_url,
      address_line_1,
      address_line_2,
      phonenumber,
      email,
      ...properties
    } = feature.properties;

    const displayName = name || '';
    const displayPhonenumber = phonenumber || '';
    const displayEmail = email || '';

    const title = location_url
      ? createElement(
          'a',
          {
            href: location_url,
            class: 'link link--primary',
            'aria-label': displayName,
            title: displayName,
          },
          [displayName]
        )
      : displayName;

    return createElement('div', {}, [
      createElement('div', { class: 'leaflet-content-name' }, [
        createElement('h4', { class: 'utrecht-heading-4' }, [title]),
      ]),
      createElement(
        'div',
        { class: 'leaflet-content-details container--no-margin' },
        [
          createElement('nl-paragraph', {}, [address_line_1 || '']),
          createElement('nl-paragraph', {}, [address_line_2 || '']),
          createElement(
            'a',
            {
              href: `tel:${displayPhonenumber}`,
              class: 'link link--secondary',
              'aria-label': displayPhonenumber,
              title: displayPhonenumber,
            },
            [
              createElement('span', { class: 'link__text' }, [
                displayPhonenumber,
              ]),
            ]
          ),
          createElement(
            'a',
            {
              href: `mailto:${displayEmail}`,
              class: 'link link--secondary',
              'aria-label': displayEmail,
              title: displayEmail,
            },
            [createElement('span', { class: 'link__text' }, [displayEmail])]
          ),
        ]
      ),
    ]);
  }
}

// Start!
[...LEAFLET_MAPS].forEach((leafletNode) => new Map(leafletNode));
