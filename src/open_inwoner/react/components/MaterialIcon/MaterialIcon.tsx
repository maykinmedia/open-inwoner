import clsx from 'clsx';
import { AnyComponent as AC } from 'preact';
import './MaterialIcon.scss';
import { normalizeBoolean } from '@react/lib/attributes/attribute';
import { BooleanLike } from '@react/types/attributes';

export interface MaterialIconProps {
  name: string;
  outlined?: boolean;
  extraClassName?: string[];
  small?: BooleanLike;
}

/**
 * Material Icons component
 * Icons should never be clickable (aria-hidden="true"), always surround with buttons
 */
const MaterialIcon: AC<MaterialIconProps> = ({
  name,
  outlined = true,
  extraClassName,
  small = false,
}) => (
  <span
    className={clsx(
      {
        ['material-icons']: !outlined,
        ['material-icons-outlined']: outlined,
        ['material-icons--small']: normalizeBoolean(small),
      },
      extraClassName
    )}
    aria-hidden="true"
  >
    {name}
  </span>
);

export default MaterialIcon;
