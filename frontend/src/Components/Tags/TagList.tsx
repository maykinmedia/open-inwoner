import React, {ReactElement} from 'react';
import {Tag} from './Tag';
import {iTag} from '../../types/pdc';
import './TagList.scss';


interface iTagListProps {
  tags?: Array<iTag>
}


/**
 * Returns list containing multiple tags.
 * @param {iTagListProps} props
 * @return {ReactElement}
 */
export function TagList(props: iTagListProps): ReactElement {
  return (
    <aside className="tag-list">
      <ul className="tag-list__list">
        {props.tags?.map((tag: iTag) => (
          <li key={tag.pk as any} className="tag-list__list-item">
            <Tag tag={tag}/>
          </li>
        ))}
      </ul>
    </aside>
  );
}
