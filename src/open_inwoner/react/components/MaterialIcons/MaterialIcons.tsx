import React from 'react'

export interface MaterialIconProps {
  name: string
}

// Material Icons component
export const MaterialIcon: React.FC<MaterialIconProps> = ({ name }) => (
  <span className="material-icons-outlined" aria-hidden="true">
    {name}
  </span>
)
