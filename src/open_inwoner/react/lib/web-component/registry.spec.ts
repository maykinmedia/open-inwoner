import { describe, expect, it } from 'vitest';
import { WebComponentLoader } from './loader';
import { WEB_COMPONENT_REGISTRY } from './registry';

describe('WEB_COMPONENT_REGISTRY', () => {
  it('should exist an is equal to WebComponentLoader.registry', () => {
    expect(WebComponentLoader.registry).toBeDefined();
    expect(WEB_COMPONENT_REGISTRY).toBeDefined();

    // Assert that WEB_COMPONENT_REGISTRY and WebComponentLoader.registry are object's.
    expect(typeof WEB_COMPONENT_REGISTRY).toBe('object');
    expect(typeof WebComponentLoader.registry).toBe('object');

    expect(WEB_COMPONENT_REGISTRY).toEqual(WebComponentLoader.registry);
  });

  it('should contain web component definitions', () => {
    const registry = WebComponentLoader.registry;
    const tagNames = Object.keys(
      registry
    ) as (keyof typeof WebComponentLoader.registry)[];

    expect(tagNames.length).toBeGreaterThan(0);

    tagNames.forEach((tagName) => {
      const definition = registry[tagName];
      expect(definition).toHaveProperty('tagName');
      expect(definition).toHaveProperty('propNames');
      expect(definition).toHaveProperty('importer');
    });
  });

  it('should have known web component definitions', () => {
    const tagNames = Object.keys(WebComponentLoader.registry);
    expect(tagNames).toContain('material-icon');
    expect(tagNames).toContain('oip-action-list');
    expect(tagNames).toContain('side-navigation');
    expect(tagNames).toContain('kvk-branch-selector');
  });

  it('should have valid importer functions', () => {
    const registry = WebComponentLoader.registry;
    const tagNames = Object.keys(
      registry
    ) as (keyof typeof WebComponentLoader.registry)[];
    tagNames.forEach((tagName) => {
      expect(typeof registry[tagName].importer).toBe('function');
    });
  });

  it('should have propNames as array', () => {
    const registry = WebComponentLoader.registry;
    const tagNames = Object.keys(
      registry
    ) as (keyof typeof WebComponentLoader.registry)[];
    tagNames.forEach((tagName) => {
      expect(Array.isArray(registry[tagName].propNames)).toBe(true);
    });
  });
});
