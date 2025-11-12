import React from 'react';

export interface MaterialIconProps {
  name: string;
}

/**
 * Material Icons component
 * Icons should never be clickable (aria-hidden="true"), always surround with buttons
 */
export const MaterialIcon: React.FC<MaterialIconProps> = ({ name }) => (
  <span className="material-icons-outlined" aria-hidden="true">
    {name}
  </span>
);
