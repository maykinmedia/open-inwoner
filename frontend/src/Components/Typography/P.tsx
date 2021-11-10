import 'react';
import './P.scss';

interface iBodyProps {
  children?: any,
}

/**
 * p element.
 */
export const P = (props: iBodyProps) => {
  return (
    <p className="p">{props.children}</p>
  );
}
