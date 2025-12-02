import { FC } from 'preact';

export interface MaterialIconProps {
  name: string;
}

/**
 * Material Icons component
 * Icons should never be clickable (aria-hidden="true"), always surround with buttons
 */
const MaterialIcon: FC<MaterialIconProps> = ({ name }) => (
  <span className="material-icons-outlined" aria-hidden="true">
    {name}
  </span>
);

export default MaterialIcon;
