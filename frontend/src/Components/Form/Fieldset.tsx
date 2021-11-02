import { Direction } from '../../types/direction';

import './Fieldset.scss';

interface FieldsetProps {
    direction: Direction,
    children?: any,
}

export function Fieldset(props:FieldsetProps) {
  return (
    <fieldset
      className={`fieldset fieldset--${props.direction}`}
    >
      { props.children }
    </fieldset>
  );
}
