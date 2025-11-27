import { registerWebComponent } from '@react/lib/web-component/utils';
import { FunctionComponent as FC } from 'preact';
import { webComponentName } from '.';

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

export function loader() {
  return registerWebComponent(MaterialIcon, webComponentName, ['name'], {
    shadow: false,
  });
}

export default MaterialIcon;
