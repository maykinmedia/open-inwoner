import { WebComponentDefinition } from '@react/lib/web-component';

export const FORM_COMPONENT_DEFINITION: WebComponentDefinition<'oip-form'> = {
  tagName: 'oip-form',
  propNames: [],
  options: { shadow: true },
  subComponents: [
    'oip-filters',
    'oip-filter-bar',
    'oip-filter-chips',
    'oip-form-button',
    'oip-select',
    'oip-select-option',
  ],
  importer: () => import('./FormComponent'),
};

export const FORM_BUTTON_DEFINITION: WebComponentDefinition<'oip-form-button'> =
  {
    tagName: 'oip-form-button',
    propNames: [],
    options: { shadow: true },
    importer: () => import('./FormButton'),
  };

export const FORM_FILTERS_DEFINITION: WebComponentDefinition<'oip-filters'> = {
  tagName: 'oip-filters',
  propNames: [],
  options: { shadow: true },
  importer: () => import('./FormFilters'),
};

export const FORM_FILTER_BAR_DEFINITION: WebComponentDefinition<'oip-filter-bar'> =
  {
    tagName: 'oip-filter-bar',
    propNames: [],
    options: { shadow: true },
    importer: () => import('./FormFilterBar'),
  };

export const FORM_FILTER_CHIPS_DEFINITION: WebComponentDefinition<'oip-filter-chips'> =
  {
    tagName: 'oip-filter-chips',
    propNames: [],
    options: { shadow: true },
    importer: () => import('./FormFilterChips'),
  };
