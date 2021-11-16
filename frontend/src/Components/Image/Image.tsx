import React, {ReactElement} from 'react';
import './Image.scss';

interface iImageProps {
  alt: string,
  src: string,
}

export function Image(props: iImageProps): ReactElement {
  const {alt, src, ..._props} = props;
  return (
    <img className="image" alt={alt} src={src} {..._props}/>
  );
}
