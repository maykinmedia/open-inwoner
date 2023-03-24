import escapeHTML from 'escape-html'
import 'leaflet'
import { RD_CRS } from './rd'
import { isMobile } from '../../lib/device/is-mobile'

/** @type {NodeListOf<Element>} All the leaflet maps. */
const LEAFLET_MAPS = document.querySelectorAll('.map__leaflet')

/**
 * Renders a (Leaflet) map.
 */
class Map {
  /**
   * Constructor method.
   * @param {HTMLElement} node
   */
  constructor(node) {
    this.node = node
    this.lat = node.dataset.lat || 52
    this.lng = node.dataset.lng || 11
    this.zoom = node.dataset.zoom || 13

    const mapOptions = {
      center: L.latLng(this.lat, this.lng),
      zoom: this.zoom,
      crs: RD_CRS,
    }

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
    }

    this.map = L.map(this.node, mapOptions)
    const tileLayer = L.tileLayer(tileConfig.url, tileConfig.options)
    tileLayer.addTo(this.map)
    this.addGeoJSON()

    if (isMobile()) {
      this.map.dragging.disable()
    }
  }

  /**
   * Adds geoJSON found in data-geojson-feature-collection.
   */
  addGeoJSON() {
    this.geoJSON = this.node.dataset.geojsonFeatureCollection

    if (!this.geoJSON) {
      return
    }

    const data = JSON.parse(this.geoJSON)
    L.geoJSON(data, {
      onEachFeature: (feature, layer) =>
        layer.bindPopup(this.featureToHTML(feature), {
          maxWidth: 300,
        }),
    }).addTo(this.map)
  }

  /**
   * Renders a feature as html.
   * @param {Object} feature
   * @return {string}
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
    } = feature.properties

    const displayName = name ? escapeHTML(name) : ''
    const locationDetailView = location_url ? escapeHTML(location_url) : ''
    const displayAddress1 = address_line_1 ? escapeHTML(address_line_1) : ''
    const displayAddress2 = address_line_2 ? escapeHTML(address_line_2) : ''
    const displayPhonenumber = phonenumber ? escapeHTML(phonenumber) : ''
    const displayEmail = email ? escapeHTML(email) : ''
    let title = ''

    if (locationDetailView) {
      title = `
        <a href="${locationDetailView}" class="link link--primary" aria-label=${displayName} title=${displayName}>
          ${displayName}
        </a>
      `
    } else {
      title = displayName
    }

    return `
      <div class="leaflet-content-name">
        <h4 class="h4">
          ${title}
        </h4>
      </div>
      <div class="leaflet-content-details p--no-margin">
        <p class="p">${displayAddress1}</p>
        <p class="p">${displayAddress2}</p>
        <a href="tel:${displayPhonenumber}" class="link link--primary" aria-label=${displayPhonenumber} title=${displayPhonenumber}>
          <span class="link__text">${displayPhonenumber}</span>
        </a>
        <a href="mailto:${displayEmail}" class="link link--primary" aria-label=${displayEmail} title=${displayEmail}>
          <span class="link__text">${displayEmail}</span>
        </a>
      </div>
    `
  }
}

// Start!
;[...LEAFLET_MAPS].forEach((leafletNode) => new Map(leafletNode))
