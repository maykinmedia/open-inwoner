import React, {ReactElement} from 'react';
import {iTag} from '../../types/pdc';
import './Tag.scss';


interface iTagProps {
  tag: iTag
}


/**
 * Renders a tag.
 * @param {iTagProps} props
 * @return {ReactElement}
 */
export function Tag(props: iTagProps): ReactElement {
  const {tag, ..._props} = props;

  return (
    <span className="tag" {..._props}>{tag.name}</span>
  );
}
