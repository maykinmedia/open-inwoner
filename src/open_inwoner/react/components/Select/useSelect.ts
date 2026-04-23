/**
 * Public hook for programmatic use of a select field bound to FormContext.
 * Use this inside preact components that need direct access to select logic
 * without rendering the oip-select web component.
 *
 * Example:
 *   const { selectedValues, toggle, isOpen, toggleDropdown } = useSelect('status', true, 'open');
 */
export { useSelectProvider as useSelect } from './useSelectProvider';
