import clsx from 'clsx';
import { AnyComponent as AC } from 'preact';

export interface MaterialIconProps {
  name: string;
  outlined?: boolean;
  extraClassName?: string[];
}

/**
 * Material Icons component
 * Icons should never be clickable (aria-hidden="true"), always surround with buttons
 */
const MaterialIcon: AC<MaterialIconProps> = ({
  name,
  outlined = true,
  extraClassName,
}) => (
  <span
    className={clsx(
      {
        ['material-icons']: !outlined,
        ['material-icons-outlined']: outlined,
      },
      extraClassName
    )}
    aria-hidden="true"
  >
    {name}
  </span>
);

export default MaterialIcon;
