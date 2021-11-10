import 'react';
import './H4.scss';


interface iHeadingProps {
  children?: any,
}

/**
 * h4 element.
 */
export const H4 = (props: iHeadingProps) => {
  return (
    <h4 className="h4">{props.children}</h4>
  );
}
