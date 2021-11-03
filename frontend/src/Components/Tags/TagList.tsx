import React from 'react';
import { Tag } from './Tag';
import { iTag } from '../../types/pdc';

import './TagList.scss';

interface TagListProps {
    tags?: Array<iTag>
}

export function TagList(props:TagListProps) {
  return (
    <div className="tag-list">
      {props.tags?.map((tag:iTag) => <Tag key={`${tag.pk}`}>{tag.name}</Tag>)}
    </div>
  );
}
