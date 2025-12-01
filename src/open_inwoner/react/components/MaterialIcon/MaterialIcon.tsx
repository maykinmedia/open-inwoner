import { FunctionComponent as FC } from 'preact';
import { WEB_COMPONENT_NAME } from '.';
import { WebComponentLoader } from '@react/lib/web-component/loader';

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

export const loader = WebComponentLoader.loadWC(
  WEB_COMPONENT_NAME,
  MaterialIcon
);

export default MaterialIcon;
